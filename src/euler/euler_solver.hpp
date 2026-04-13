#pragma once

#include "core/types.hpp"
#include "core/vec.hpp"
#include "core/grid.hpp"
#include "core/eos.hpp"
#include "core/boundary.hpp"
#include "euler/euler_flux.hpp"
#include "euler/hancock.hpp"
#include "euler/hllc.hpp"

#include <vector>
#include <cmath>
#include <algorithm>
#include <limits>

namespace hrsc {

template <typename Real>
class EulerSolver {
    Grid2D<Real, 4> m_grid;
    Real m_xmin;
    Real m_ymin;
    Real m_gamma;
    Real m_cfl;
    Real m_t_end;
    Real m_time;
    int  m_step;

    // X-direction sweep: compute x-interface fluxes and update conserved variables.
    void x_sweep(Real dt) {
        auto gv = m_grid.view();
        int nx = gv.nx;
        int ny = gv.ny;
        int n_interfaces = nx + 1;

        for (int j = 0; j < ny; ++j) {
            std::vector<Vec<Real, 4>> flux(n_interfaces);

            for (int k = 0; k < n_interfaces; ++k) {
                int iL = k - 1;
                int iR = k;

                Vec<Real, 4> qL_left{}, qL_right{};
                Vec<Real, 4> qR_left{}, qR_right{};

                muscl_hancock_x(gv, iL, j, dt, m_gamma, qL_left, qL_right);
                muscl_hancock_x(gv, iR, j, dt, m_gamma, qR_left, qR_right);

                flux[k] = hllc_flux(qL_right, qR_left, m_gamma);
            }

            Real dtdx = dt / gv.dx;
            for (int i = 0; i < nx; ++i) {
                for (int v = 0; v < 4; ++v) {
                    gv(i, j, v) -= dtdx * (flux[i + 1][v] - flux[i][v]);
                }
            }
        }
    }

    // Y-direction sweep: compute y-interface fluxes and update conserved variables.
    void y_sweep(Real dt) {
        auto gv = m_grid.view();
        int nx = gv.nx;
        int ny = gv.ny;
        int n_interfaces = ny + 1;

        for (int i = 0; i < nx; ++i) {
            std::vector<Vec<Real, 4>> flux(n_interfaces);

            for (int k = 0; k < n_interfaces; ++k) {
                int jB = k - 1;  // cell below interface
                int jT = k;      // cell above interface

                Vec<Real, 4> qB_bot{}, qB_top{};
                Vec<Real, 4> qT_bot{}, qT_top{};

                muscl_hancock_y(gv, i, jB, dt, m_gamma, qB_bot, qB_top);
                muscl_hancock_y(gv, i, jT, dt, m_gamma, qT_bot, qT_top);

                // Rotate → HLLC → rotate back
                flux[k] = swap_momentum(
                    hllc_flux(swap_momentum(qB_top), swap_momentum(qT_bot), m_gamma));
            }

            Real dtdy = dt / gv.dy;
            for (int j = 0; j < ny; ++j) {
                for (int v = 0; v < 4; ++v) {
                    gv(i, j, v) -= dtdy * (flux[j + 1][v] - flux[j][v]);
                }
            }
        }
    }

public:
    // 2D constructor
    EulerSolver(int nx, int ny, Real dx, Real dy,
                Real xmin, Real ymin,
                Real gamma, Real cfl, Real t_end)
        : m_grid(nx, ny),
          m_xmin(xmin),
          m_ymin(ymin),
          m_gamma(gamma),
          m_cfl(cfl),
          m_t_end(t_end),
          m_time(Real(0)),
          m_step(0)
    {
        m_grid.dx = dx;
        m_grid.dy = dy;
    }

    // 1D convenience constructor
    EulerSolver(int nx, Real dx, Real xmin, Real gamma, Real cfl, Real t_end)
        : EulerSolver(nx, 1, dx, dx, xmin, Real(0), gamma, cfl, t_end)
    {}

    GridView<Real, 4> grid_view() {
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
        Real max_Sx = std::numeric_limits<Real>::min();
        Real max_Sy = std::numeric_limits<Real>::min();

        for (int j = 0; j < ny; ++j) {
            for (int i = 0; i < nx; ++i) {
                Vec<Real, 4> cons;
                for (int v = 0; v < 4; ++v) cons[v] = gv(i, j, v);

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
        auto gv = m_grid.view();

        apply_outflow_bc(gv);

        Real dt = compute_dt();
        if (dt <= Real(0)) return;

        if (m_grid.ny == 1) {
            // 1D path: x-sweep only, exact backward compatibility
            x_sweep(dt);
        } else {
            // 2D path: alternating Godunov splitting
            if (m_step % 2 == 0) {
                x_sweep(dt);
                apply_outflow_bc(gv);
                y_sweep(dt);
            } else {
                y_sweep(dt);
                apply_outflow_bc(gv);
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
};

} // namespace hrsc
