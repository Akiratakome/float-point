// Out-of-line definitions for EulerSolver<Real>. The header only declares
// the class; method bodies live here so the solver compiles once per
// precision per binary (compile-time win) and so a "precision build"
// honestly contains only the requested instantiation's code path.
//
// Free function templates (hllc_flux, rusanov_flux, muscl_hancock_*,
// euler_flux_*, exact_riemann_sample) remain header-only on purpose:
//   - unit tests instantiate them directly,
//   - they are small enough that inlining matters,
//   - keeping them header-only is needed for future GPU kernels.
//
// Explicit instantiations at end of file: float and double only.

#include "euler/euler_solver.hpp"

#ifdef HRSC_ENABLE_PROFILING
#include "utils/timer.hpp"
#endif

namespace hrsc {

template <typename Real>
EulerSolver<Real>::EulerSolver(int nx, int ny, Real dx, Real dy,
                               Real xmin, Real ymin,
                               Real gamma, Real cfl, TimeReal t_end,
                               FluxScheme flux,
                               BoundaryType bc_x,
                               BoundaryType bc_y)
    : m_grid(nx, ny),
      m_xmin(xmin),
      m_ymin(ymin),
      m_gamma(gamma),
      m_cfl(cfl),
      m_t_end(t_end),
      m_time(TimeReal(0)),
      m_kahan_c(TimeReal(0)),
      m_step(0),
      m_flux(flux),
      m_bc_x(bc_x),
      m_bc_y(bc_y)
{
    m_grid.dx = dx;
    m_grid.dy = dy;
}

template <typename Real>
EulerSolver<Real>::EulerSolver(int nx, Real dx, Real xmin,
                               Real gamma, Real cfl, TimeReal t_end,
                               FluxScheme flux,
                               BoundaryType bc_x,
                               BoundaryType bc_y)
    : EulerSolver(nx, 1, dx, dx, xmin, Real(0), gamma, cfl, t_end, flux, bc_x, bc_y)
{}

template <typename Real>
void EulerSolver<Real>::apply_boundary_conditions()
{
#ifdef HRSC_ENABLE_PROFILING
    ScopedTimer __prof("bc", m_prof_);
#endif
    auto gv = m_grid.view();
    // Euler-specific reflective flip lists. MHD will live in its own
    // solver class with its own flip lists ({RHOU, BX}, {RHOV, BY}).
    static constexpr std::array<int, 1> kFlipX = {RHOU};
    static constexpr std::array<int, 1> kFlipY = {RHOV};

    // X-pass first so the Y-pass can read x-ghost columns when filling
    // corner cells (matches legacy ordering).
    switch (m_bc_x) {
        case BoundaryType::Outflow:    apply_outflow_bc(gv, Axis::X); break;
        case BoundaryType::Periodic:   apply_periodic_bc(gv, Axis::X); break;
        case BoundaryType::Reflective: apply_reflective_bc(gv, Axis::X, kFlipX); break;
    }
    switch (m_bc_y) {
        case BoundaryType::Outflow:    apply_outflow_bc(gv, Axis::Y); break;
        case BoundaryType::Periodic:   apply_periodic_bc(gv, Axis::Y); break;
        case BoundaryType::Reflective: apply_reflective_bc(gv, Axis::Y, kFlipY); break;
    }
}

// X-direction sweep: compute x-interface fluxes and update conserved variables.
// dt arrives in TimeReal=double; we down-cast to Real exactly once at entry
// so the rest of the sweep keeps the established Week-3 numerics intact.
// This single down-cast is the only Real/TimeReal coupling point.
template <typename Real>
void EulerSolver<Real>::x_sweep(TimeReal dt)
{
    const Real dt_real = static_cast<Real>(dt);
    auto gv = m_grid.view();
#ifdef HRSC_ENABLE_PROFILING
    ScopedTimer __prof_sweep("sweep", m_prof_);
#endif
    int nx = gv.nx;
    int ny = gv.ny;
    int n_interfaces = nx + 1;
#ifdef HRSC_ENABLE_PROFILING
    std::vector<std::vector<Vec<Real, EulerNVars>>> fluxes(
        ny, std::vector<Vec<Real, EulerNVars>>(n_interfaces));

    {
        ScopedTimer __prof_flux("flux", m_prof_);
        #pragma omp parallel for schedule(static)
        for (int j = 0; j < ny; ++j) {
            auto& flux = fluxes[j];

            for (int k = 0; k < n_interfaces; ++k) {
                int iL = k - 1;
                int iR = k;

                Vec<Real, EulerNVars> qL_left{}, qL_right{};
                Vec<Real, EulerNVars> qR_left{}, qR_right{};

                muscl_hancock_x(gv, iL, j, dt_real, m_gamma, qL_left, qL_right);
                muscl_hancock_x(gv, iR, j, dt_real, m_gamma, qR_left, qR_right);

                flux[k] = (m_flux == FluxScheme::Rusanov)
                    ? rusanov_flux(qL_right, qR_left, m_gamma)
                    : hllc_flux(qL_right, qR_left, m_gamma);
            }
        }
    }

    {
        ScopedTimer __prof_update("update", m_prof_);
        #pragma omp parallel for schedule(static)
        for (int j = 0; j < ny; ++j) {
            const auto& flux = fluxes[j];
            Real dtdx = dt_real / gv.dx;
            for (int i = 0; i < nx; ++i) {
                for (int v = 0; v < EulerNVars; ++v) {
                    gv(i, j, v) -= dtdx * (flux[i + 1][v] - flux[i][v]);
                }
            }
        }
    }
#else
    #pragma omp parallel for schedule(static)
    for (int j = 0; j < ny; ++j) {
        std::vector<Vec<Real, EulerNVars>> flux(n_interfaces);

        for (int k = 0; k < n_interfaces; ++k) {
            int iL = k - 1;
            int iR = k;

            Vec<Real, EulerNVars> qL_left{}, qL_right{};
            Vec<Real, EulerNVars> qR_left{}, qR_right{};

            muscl_hancock_x(gv, iL, j, dt_real, m_gamma, qL_left, qL_right);
            muscl_hancock_x(gv, iR, j, dt_real, m_gamma, qR_left, qR_right);

            flux[k] = (m_flux == FluxScheme::Rusanov)
                ? rusanov_flux(qL_right, qR_left, m_gamma)
                : hllc_flux(qL_right, qR_left, m_gamma);
        }

        Real dtdx = dt_real / gv.dx;
        for (int i = 0; i < nx; ++i) {
            for (int v = 0; v < EulerNVars; ++v) {
                gv(i, j, v) -= dtdx * (flux[i + 1][v] - flux[i][v]);
            }
        }
    }
#endif
}

// Y-direction sweep: compute y-interface fluxes and update conserved variables.
// muscl_hancock_y uses euler_flux_y internally for the predictor half-step.
// The HLLC corrector reuses the x-direction solver via momentum rotation.
template <typename Real>
void EulerSolver<Real>::y_sweep(TimeReal dt)
{
    const Real dt_real = static_cast<Real>(dt);
    auto gv = m_grid.view();
#ifdef HRSC_ENABLE_PROFILING
    ScopedTimer __prof_sweep("sweep", m_prof_);
#endif
    int nx = gv.nx;
    int ny = gv.ny;
    int n_interfaces = ny + 1;
#ifdef HRSC_ENABLE_PROFILING
    std::vector<std::vector<Vec<Real, EulerNVars>>> fluxes(
        nx, std::vector<Vec<Real, EulerNVars>>(n_interfaces));

    {
        ScopedTimer __prof_flux("flux", m_prof_);
        #pragma omp parallel for schedule(static)
        for (int i = 0; i < nx; ++i) {
            auto& flux = fluxes[i];

            for (int k = 0; k < n_interfaces; ++k) {
                int jB = k - 1;  // cell below interface
                int jT = k;      // cell above interface

                Vec<Real, EulerNVars> qB_bot{}, qB_top{};
                Vec<Real, EulerNVars> qT_bot{}, qT_top{};

                muscl_hancock_y(gv, i, jB, dt_real, m_gamma, qB_bot, qB_top);
                muscl_hancock_y(gv, i, jT, dt_real, m_gamma, qT_bot, qT_top);

                // Rotate -> flux -> rotate back
                auto rotL = swap_momentum(qB_top);
                auto rotR = swap_momentum(qT_bot);
                auto f_iface = (m_flux == FluxScheme::Rusanov)
                    ? rusanov_flux(rotL, rotR, m_gamma)
                    : hllc_flux(rotL, rotR, m_gamma);
                flux[k] = swap_momentum(f_iface);
            }
        }
    }

    {
        ScopedTimer __prof_update("update", m_prof_);
        #pragma omp parallel for schedule(static)
        for (int i = 0; i < nx; ++i) {
            const auto& flux = fluxes[i];
            Real dtdy = dt_real / gv.dy;
            for (int j = 0; j < ny; ++j) {
                for (int v = 0; v < EulerNVars; ++v) {
                    gv(i, j, v) -= dtdy * (flux[j + 1][v] - flux[j][v]);
                }
            }
        }
    }
#else
    #pragma omp parallel for schedule(static)
    for (int i = 0; i < nx; ++i) {
        std::vector<Vec<Real, EulerNVars>> flux(n_interfaces);

        for (int k = 0; k < n_interfaces; ++k) {
            int jB = k - 1;  // cell below interface
            int jT = k;      // cell above interface

            Vec<Real, EulerNVars> qB_bot{}, qB_top{};
            Vec<Real, EulerNVars> qT_bot{}, qT_top{};

            muscl_hancock_y(gv, i, jB, dt_real, m_gamma, qB_bot, qB_top);
            muscl_hancock_y(gv, i, jT, dt_real, m_gamma, qT_bot, qT_top);

            // Rotate -> flux -> rotate back
            auto rotL = swap_momentum(qB_top);
            auto rotR = swap_momentum(qT_bot);
            auto f_iface = (m_flux == FluxScheme::Rusanov)
                ? rusanov_flux(rotL, rotR, m_gamma)
                : hllc_flux(rotL, rotR, m_gamma);
            flux[k] = swap_momentum(f_iface);
        }

        Real dtdy = dt_real / gv.dy;
        for (int j = 0; j < ny; ++j) {
            for (int v = 0; v < EulerNVars; ++v) {
                gv(i, j, v) -= dtdy * (flux[j + 1][v] - flux[j][v]);
            }
        }
    }
#endif
}

// Compute stable time step: dt = CFL * min(dx/Sx, dy/Sy)
// Wave speeds are computed in Real (state precision) and the resulting
// dt promoted to TimeReal=double for the time accumulator.
template <typename Real>
TimeReal EulerSolver<Real>::compute_dt() const
{
#ifdef HRSC_ENABLE_PROFILING
    ScopedTimer __prof("cfl", m_prof_);
#endif
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

    TimeReal dt = static_cast<TimeReal>(m_cfl)
                * std::min(static_cast<TimeReal>(gv.dx) / static_cast<TimeReal>(max_Sx),
                           static_cast<TimeReal>(gv.dy) / static_cast<TimeReal>(max_Sy));

    if (m_time + dt > m_t_end) {
        dt = m_t_end - m_time;
    }

    return dt;
}

template <typename Real>
void EulerSolver<Real>::step()
{
    apply_boundary_conditions();

    TimeReal dt = compute_dt();
    if (dt <= TimeReal(0)) return;

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

    // Kahan compensated summation: keeps full double precision for the
    // time accumulator even after ~1e8 steps. m_kahan_c carries the
    // running "lost bits" correction. Without this, naive m_time += dt
    // loses bits monotonically once t >> dt.
    TimeReal y     = dt - m_kahan_c;
    TimeReal t_new = m_time + y;
    m_kahan_c = (t_new - m_time) - y;
    m_time    = t_new;

    m_step++;
}

template <typename Real>
void EulerSolver<Real>::run()
{
    while (m_time < m_t_end) {
        step();
    }
}

// Run with a wall-clock-throttled progress line on stderr.
// Line format: "[progress] step=K t=T/T_end (P%) elapsed=Ws eta=Ws steps/s=R"
// Emits one line at start, every progress_interval_s, and one at finish.
template <typename Real>
void EulerSolver<Real>::run(double progress_interval_s)
{
    if (progress_interval_s <= 0.0) { run(); return; }
    using clk = std::chrono::steady_clock;
    auto t0 = clk::now();
    auto t_last_print = t0;
    int  step_at_last_print = m_step;
    auto print_line = [&](const char* tag) {
        auto now = clk::now();
        double elapsed = std::chrono::duration<double>(now - t0).count();
        double t_frac = (m_t_end > TimeReal(0))
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

// ---------------------------------------------------------------------------
// Explicit instantiation. Per overall.md "Precision-Generic Design", the
// solver supports float and double. long double / __float128 (quad) is
// deferred to Week 17: it requires Boost.Multiprecision or libquadmath
// wiring and is scoped to 1D CPU runs only, so emitting an instantiation
// here would be misleading. Attempting `EulerSolver<long double>` from a
// translation unit will cleanly fail at link time with "undefined
// reference", which is exactly the strict precision control we want.
// ---------------------------------------------------------------------------
template class EulerSolver<float>;
template class EulerSolver<double>;

} // namespace hrsc
