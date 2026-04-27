#pragma once

#include "core/types.hpp"
#include "core/vec.hpp"
#include "core/grid.hpp"
#include "core/eos.hpp"
#include "core/boundary.hpp"
#include "euler/euler_flux.hpp"
#include "euler/hancock.hpp"
#include "euler/hllc.hpp"
#include "euler/rusanov.hpp"

#include <vector>
#include <cmath>
#include <algorithm>
#include <limits>
#include <chrono>
#include <cstdio>

namespace hrsc {

enum class FluxScheme { HLLC, Rusanov };
enum class BoundaryType { Outflow, Periodic, Reflective };

namespace detail {
    // ETA estimator becomes unreliable when the simulation has barely begun
    // (t / t_end too small): print "0.0s" rather than a meaningless huge number.
    constexpr double kProgressEtaMinFrac = 1e-12;
    // Wall-clock granularity floor for the per-tick rate estimate; below this
    // the steps/s computation underflows or produces nonsense due to clock noise.
    constexpr double kProgressMinIntervalSeconds = 1e-9;
}

template <typename Real>
class EulerSolver {
    Grid2D<Real, EulerNVars> m_grid;
    Real m_xmin;
    Real m_ymin;
    Real m_gamma;
    Real m_cfl;
    Real m_t_end;
    Real m_time;
    int  m_step;
    FluxScheme m_flux;
    BoundaryType m_boundary;

    void apply_boundary_conditions() {
        auto gv = m_grid.view();
        switch (m_boundary) {
            case BoundaryType::Outflow:
                apply_outflow_bc(gv);
                break;
            case BoundaryType::Periodic:
                apply_periodic_bc(gv);
                break;
            case BoundaryType::Reflective:
                apply_reflective_bc(gv);
                break;
        }
    }

    // X-direction sweep: compute x-interface fluxes and update conserved variables.
    void x_sweep(Real dt) {
        auto gv = m_grid.view();
        int nx = gv.nx;
        int ny = gv.ny;
        int n_interfaces = nx + 1;

        #pragma omp parallel for schedule(static)
        for (int j = 0; j < ny; ++j) {
            std::vector<Vec<Real, EulerNVars>> flux(n_interfaces);

            for (int k = 0; k < n_interfaces; ++k) {
                int iL = k - 1;
                int iR = k;

                Vec<Real, EulerNVars> qL_left{}, qL_right{};
                Vec<Real, EulerNVars> qR_left{}, qR_right{};

                muscl_hancock_x(gv, iL, j, dt, m_gamma, qL_left, qL_right);
                muscl_hancock_x(gv, iR, j, dt, m_gamma, qR_left, qR_right);

                flux[k] = (m_flux == FluxScheme::Rusanov)
                    ? rusanov_flux(qL_right, qR_left, m_gamma)
                    : hllc_flux(qL_right, qR_left, m_gamma);
            }

            Real dtdx = dt / gv.dx;
            for (int i = 0; i < nx; ++i) {
                for (int v = 0; v < EulerNVars; ++v) {
                    gv(i, j, v) -= dtdx * (flux[i + 1][v] - flux[i][v]);
                }
            }
        }
    }

    // Y-direction sweep: compute y-interface fluxes and update conserved variables.
    // muscl_hancock_y uses euler_flux_y internally for the predictor half-step.
    // The HLLC corrector reuses the x-direction solver via momentum rotation.
    void y_sweep(Real dt) {
        auto gv = m_grid.view();
        int nx = gv.nx;
        int ny = gv.ny;
        int n_interfaces = ny + 1;

        #pragma omp parallel for schedule(static)
        for (int i = 0; i < nx; ++i) {
            std::vector<Vec<Real, EulerNVars>> flux(n_interfaces);

            for (int k = 0; k < n_interfaces; ++k) {
                int jB = k - 1;  // cell below interface
                int jT = k;      // cell above interface

                Vec<Real, EulerNVars> qB_bot{}, qB_top{};
                Vec<Real, EulerNVars> qT_bot{}, qT_top{};

                muscl_hancock_y(gv, i, jB, dt, m_gamma, qB_bot, qB_top);
                muscl_hancock_y(gv, i, jT, dt, m_gamma, qT_bot, qT_top);

                // Rotate → flux → rotate back
                auto rotL = swap_momentum(qB_top);
                auto rotR = swap_momentum(qT_bot);
                auto f_iface = (m_flux == FluxScheme::Rusanov)
                    ? rusanov_flux(rotL, rotR, m_gamma)
                    : hllc_flux(rotL, rotR, m_gamma);
                flux[k] = swap_momentum(f_iface);
            }

            Real dtdy = dt / gv.dy;
            for (int j = 0; j < ny; ++j) {
                for (int v = 0; v < EulerNVars; ++v) {
                    gv(i, j, v) -= dtdy * (flux[j + 1][v] - flux[j][v]);
                }
            }
        }
    }

public:
    // 2D constructor
    EulerSolver(int nx, int ny, Real dx, Real dy,
                Real xmin, Real ymin,
                Real gamma, Real cfl, Real t_end,
                FluxScheme flux = FluxScheme::HLLC,
                BoundaryType boundary = BoundaryType::Outflow)
        : m_grid(nx, ny),
          m_xmin(xmin),
          m_ymin(ymin),
          m_gamma(gamma),
          m_cfl(cfl),
          m_t_end(t_end),
          m_time(Real(0)),
          m_step(0),
          m_flux(flux),
          m_boundary(boundary)
    {
        m_grid.dx = dx;
        m_grid.dy = dy;
    }

    // 1D convenience constructor
    EulerSolver(int nx, Real dx, Real xmin, Real gamma, Real cfl, Real t_end,
                FluxScheme flux = FluxScheme::HLLC,
                BoundaryType boundary = BoundaryType::Outflow)
        : EulerSolver(nx, 1, dx, dx, xmin, Real(0), gamma, cfl, t_end, flux, boundary)
    {}

    GridView<Real, EulerNVars> grid_view() {
        return m_grid.view();
    }

    Real time() const { return m_time; }
    int  step_count() const { return m_step; }
    Real xmin() const { return m_xmin; }
    Real ymin() const { return m_ymin; }

    // Compute stable time step: dt = CFL * min(dx/Sx, dy/Sy)
    Real compute_dt() const {
        auto gv = m_grid.view();
        int nx = gv.nx;
        int ny = gv.ny;
        Real max_Sx = std::numeric_limits<Real>::lowest();
        Real max_Sy = std::numeric_limits<Real>::lowest();

        #pragma omp parallel for collapse(2) reduction(max:max_Sx,max_Sy) schedule(static)
        for (int j = 0; j < ny; ++j) {
            for (int i = 0; i < nx; ++i) {
                Vec<Real, EulerNVars> cons;
                for (int v = 0; v < EulerNVars; ++v) cons[v] = gv(i, j, v);

                Real rho = cons[RHO];
                Real u   = cons[RHOU] / rho;
                Real vel_v = cons[RHOV] / rho;
                Real p   = pressure(cons, m_gamma);
                Real a   = sound_speed(rho, p, m_gamma);

                max_Sx = std::max(max_Sx, std::abs(u) + a);
                max_Sy = std::max(max_Sy, std::abs(vel_v) + a);
            }
        }

        Real dt = m_cfl * std::min(gv.dx / max_Sx, gv.dy / max_Sy);

        if (m_time + dt > m_t_end) {
            dt = m_t_end - m_time;
        }

        return dt;
    }

    void step() {
        apply_boundary_conditions();

        Real dt = compute_dt();
        if (dt <= Real(0)) return;

        if (m_grid.ny == 1) {
            // 1D path: x-sweep only, exact backward compatibility
            x_sweep(dt);
        } else {
            // 2D path: alternating Godunov splitting
            if (m_step % 2 == 0) {
                x_sweep(dt);
                apply_boundary_conditions();
                y_sweep(dt);
            } else {
                y_sweep(dt);
                apply_boundary_conditions();
                x_sweep(dt);
            }
        }

        m_time += dt;
        m_step++;
    }

    void run() {
        while (m_time < m_t_end) {
            step();
        }
    }

    // Run with a wall-clock-throttled progress line on stderr.
    // progress_interval_s <= 0 disables printing (equivalent to run()).
    // Line format: "[progress] step=K t=T/T_end (P%) elapsed=Ws eta=Ws steps/s=R"
    // Emits one line at start, every progress_interval_s, and one at finish.
    void run(double progress_interval_s) {
        if (progress_interval_s <= 0.0) { run(); return; }
        using clk = std::chrono::steady_clock;
        auto t0 = clk::now();
        auto t_last_print = t0;
        int  step_at_last_print = m_step;
        auto print_line = [&](const char* tag) {
            auto now = clk::now();
            double elapsed = std::chrono::duration<double>(now - t0).count();
            double t_frac = (m_t_end > Real(0))
                ? static_cast<double>(m_time) / static_cast<double>(m_t_end)
                : 0.0;
            double eta = (t_frac > detail::kProgressEtaMinFrac) ? elapsed * (1.0 - t_frac) / t_frac : 0.0;
            double dt_interval = std::chrono::duration<double>(now - t_last_print).count();
            double steps_per_s = (dt_interval > detail::kProgressMinIntervalSeconds)
                ? (m_step - step_at_last_print) / dt_interval : 0.0;
            std::fprintf(stderr,
                "[progress:%s] step=%d t=%.6g/%.6g (%.2f%%) elapsed=%.1fs eta=%.1fs rate=%.1f steps/s\n",
                tag, m_step,
                static_cast<double>(m_time), static_cast<double>(m_t_end),
                100.0 * t_frac, elapsed, eta, steps_per_s);
            std::fflush(stderr);
        };
        print_line("start");
        while (m_time < m_t_end) {
            step();
            auto now = clk::now();
            double since_last = std::chrono::duration<double>(now - t_last_print).count();
            if (since_last >= progress_interval_s) {
                print_line("tick");
                t_last_print = now;
                step_at_last_print = m_step;
            }
        }
        print_line("done");
    }
};

} // namespace hrsc
