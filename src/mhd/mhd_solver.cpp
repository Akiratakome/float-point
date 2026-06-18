#include "mhd/mhd_solver.hpp"
#include "mhd/glm.hpp"

#include <algorithm>
#include <cmath>
#include <sstream>
#include <stdexcept>
#include <vector>

namespace hrsc {

namespace {

template <typename Real, typename Ptr>
Vec<Real, MhdNVars> load_cell(GridViewBase<Real, MhdNVars, Ptr> gv, int i, int j) {
    Vec<Real, MhdNVars> U{};
    for (int k = 0; k < MhdNVars; ++k) {
        U[k] = gv(i, j, k);
    }
    return U;
}

template <typename Real>
void store_cell(GridView<Real, MhdNVars> gv, int i, int j, const Vec<Real, MhdNVars>& U) {
    for (int k = 0; k < MhdNVars; ++k) {
        gv(i, j, k) = U[k];
    }
}

template <typename Real>
bool is_physical_state(const Vec<Real, MhdNVars>& U, Real gamma) {
    for (int k = 0; k < MhdNVars; ++k) {
        if (!std::isfinite(U[k])) {
            return false;
        }
    }
    if (!(U[MhdIdx::RHO] > Real(0))) {
        return false;
    }
    const Real p = pressure(U, gamma);
    return std::isfinite(p) && p > Real(0);
}

// State-based MUSCL-Hancock face prediction: a pure function of the three
// cells along the sweep direction and that direction's spacing h. The x-sweep
// passes cells directly; the y-sweep (Task 15) passes rotated states so
// mhd_flux_x remains the correct normal flux.
template <typename Real>
void predict_faces(const Vec<Real, MhdNVars>& Um, const Vec<Real, MhdNVars>& U0,
                   const Vec<Real, MhdNVars>& Up, Real dt, Real gamma, Real ch, Real h,
                   Vec<Real, MhdNVars>& left, Vec<Real, MhdNVars>& right) {
    const Vec<Real, MhdNVars> slope = mhd_slope(Um, U0, Up);

    left = U0 - Real(0.5) * slope;
    right = U0 + Real(0.5) * slope;

    if (!is_physical_state(left, gamma) || !is_physical_state(right, gamma)) {
        left = U0;
        right = U0;
        return;
    }

    const Vec<Real, MhdNVars> FL = mhd_flux_x(left, gamma, ch);
    const Vec<Real, MhdNVars> FR = mhd_flux_x(right, gamma, ch);
    const Real half_dtdx = Real(0.5) * dt / h;

    for (int k = 0; k < MhdNVars; ++k) {
        const Real predictor = half_dtdx * (FR[k] - FL[k]);
        left[k] -= predictor;
        right[k] -= predictor;
    }

    if (!is_physical_state(left, gamma) || !is_physical_state(right, gamma)) {
        left = U0;
        right = U0;
    }
}

template <typename Real>
void validate_physical_grid(GridView<Real, MhdNVars> gv, Real gamma) {
    for (int j = 0; j < gv.ny; ++j) {
        for (int i = 0; i < gv.nx; ++i) {
            const Vec<Real, MhdNVars> U = load_cell(gv, i, j);
            if (!is_physical_state(U, gamma)) {
                std::ostringstream msg;
                msg << "MhdSolver produced nonphysical state at i=" << i << " j=" << j
                    << " rho=" << U[MhdIdx::RHO];
                if (std::isfinite(U[MhdIdx::RHO]) && U[MhdIdx::RHO] > Real(0)) {
                    msg << " p=" << pressure(U, gamma);
                }
                throw std::runtime_error(msg.str());
            }
        }
    }
}

template <typename Real>
void zero_psi_ghosts(GridView<Real, MhdNVars> gv, Axis axis) {
    constexpr int ng = GridView<Real, MhdNVars>::ng;
    const int nx = gv.nx, ny = gv.ny;
    if (axis == Axis::X) {
        for (int j = -ng; j < ny + ng; ++j)
            for (int g = 1; g <= ng; ++g) {
                gv(-g, j, MhdIdx::PSI)         = Real(0);
                gv(nx - 1 + g, j, MhdIdx::PSI) = Real(0);
            }
    } else {
        for (int i = -ng; i < nx + ng; ++i)
            for (int g = 1; g <= ng; ++g) {
                gv(i, -g, MhdIdx::PSI)         = Real(0);
                gv(i, ny - 1 + g, MhdIdx::PSI) = Real(0);
            }
    }
}

template <typename Real>
void apply_axis_bc(GridView<Real, MhdNVars> gv, Axis axis, BoundaryType bc) {
    if (bc == BoundaryType::Outflow) {
        apply_outflow_bc(gv, axis);
        zero_psi_ghosts(gv, axis);
    } else if (bc == BoundaryType::Periodic) {
        apply_periodic_bc(gv, axis);
    } else {
        throw std::logic_error("MhdSolver supports only outflow/periodic BCs");
    }
}

} // namespace

template <typename Real>
void setup_brio_wu(GridView<Real, MhdNVars> gv, int nx, Real dx, Real xmin,
                   Real gamma, Real x0) {
    for (int i = 0; i < nx; ++i) {
        const Real x = xmin + (Real(i) + Real(0.5)) * dx;
        MhdPrim<Real> w{};
        w.rho = (x < x0) ? Real(1) : Real(0.125);
        w.vx = Real(0);
        w.vy = Real(0);
        w.vz = Real(0);
        w.Bx = Real(0.75);
        w.By = (x < x0) ? Real(1) : Real(-1);
        w.Bz = Real(0);
        w.p = (x < x0) ? Real(1) : Real(0.1);
        w.psi = Real(0);
        store_cell(gv, i, 0, prim_to_cons(w, gamma));
    }
}

template <typename Real>
MhdSolver<Real>::MhdSolver(int nx, int ny, Real dx, Real dy, Real xmin, Real ymin,
                           Real gamma, Real cfl, TimeReal t_end,
                           BoundaryType bc_x, BoundaryType bc_y, Real glm_cr)
    : m_grid(nx, ny),
      m_xmin(xmin),
      m_ymin(ymin),
      m_dx(dx),
      m_dy(dy),
      m_gamma(gamma),
      m_cfl(cfl),
      m_t_end(t_end),
      m_time(TimeReal(0)),
      m_step(0),
      m_bc_x(bc_x),
      m_ny(ny),
      m_bc_y(bc_y),
      m_glm_cr(glm_cr) {
    m_grid.dx = dx;
    m_grid.dy = dy;
}

// 1D convenience ctor: ny=1, glm_cr=0 -> no damping -> bit-identical to before.
template <typename Real>
MhdSolver<Real>::MhdSolver(int nx, Real dx, Real xmin, Real gamma, Real cfl,
                           TimeReal t_end, BoundaryType bc_x)
    : MhdSolver(nx, 1, dx, dx, xmin, Real(0), gamma, cfl, t_end,
                bc_x, BoundaryType::Outflow, Real(0)) {}

template <typename Real>
void MhdSolver<Real>::apply_bc() {
    auto gv = m_grid.view();
    apply_axis_bc(gv, Axis::X, m_bc_x);
    if (m_ny > 1) apply_axis_bc(gv, Axis::Y, m_bc_y);
}

template <typename Real>
Real MhdSolver<Real>::compute_ch() const {
    auto gv = m_grid.view();
    Real ch = Real(0);
    for (int j = 0; j < gv.ny; ++j) {
        for (int i = 0; i < gv.nx; ++i) {
            const Vec<Real, MhdNVars> U = load_cell(gv, i, j);
            const MhdPrim<Real> w = cons_to_prim(U, m_gamma);
            ch = std::max(ch, std::abs(w.vx) + fast_speed_x(w, m_gamma));
            // y-direction fast speed (By as normal field). Required for a
            // correct 2D CFL: cf_y exceeds cf_x where By -> 0. Guarded by ny>1
            // so the 1D path keeps its exact ch (and bit-identical evolution).
            if (gv.ny > 1) {
                ch = std::max(ch, std::abs(w.vy)
                                  + fast_speed_x(mhd_swap_xy_prim(w), m_gamma));
            }
        }
    }
    return ch;
}

template <typename Real>
TimeReal MhdSolver<Real>::compute_dt(Real ch) const {
    const Real denom = std::max(ch, Real(1e-30));
    TimeReal dt = static_cast<TimeReal>(m_cfl)
                * static_cast<TimeReal>(m_dx)
                / static_cast<TimeReal>(denom);
    if (m_time + dt > m_t_end) {
        dt = m_t_end - m_time;
    }
    return dt;
}

template <typename Real>
void MhdSolver<Real>::x_sweep(Real ch, TimeReal dt_time) {
    const Real dt = static_cast<Real>(dt_time);
    auto gv = m_grid.view();
    const int nx = gv.nx;
    const int ny = gv.ny;
    std::vector<Vec<Real, MhdNVars>> flux(static_cast<std::size_t>(nx + 1));

    for (int j = 0; j < ny; ++j) {
        for (int iface = 0; iface <= nx; ++iface) {
            const int iL = iface - 1;
            const int iR = iface;

            Vec<Real, MhdNVars> left_cell_left{}, left_cell_right{};
            Vec<Real, MhdNVars> right_cell_left{}, right_cell_right{};
            predict_faces(load_cell(gv, iL - 1, j), load_cell(gv, iL, j),
                          load_cell(gv, iL + 1, j), dt, m_gamma, ch, m_dx,
                          left_cell_left, left_cell_right);
            predict_faces(load_cell(gv, iR - 1, j), load_cell(gv, iR, j),
                          load_cell(gv, iR + 1, j), dt, m_gamma, ch, m_dx,
                          right_cell_left, right_cell_right);

            flux[static_cast<std::size_t>(iface)] =
                mhd_hll_flux(left_cell_right, right_cell_left, m_gamma, ch);
        }

        const Real dtdx = dt / m_dx;
        for (int i = 0; i < nx; ++i) {
            Vec<Real, MhdNVars> U = load_cell(gv, i, j);
            const auto& fL = flux[static_cast<std::size_t>(i)];
            const auto& fR = flux[static_cast<std::size_t>(i + 1)];
            for (int k = 0; k < MhdNVars; ++k) {
                U[k] -= dtdx * (fR[k] - fL[k]);
            }
            store_cell(gv, i, j, U);
        }
    }
}

template <typename Real>
void MhdSolver<Real>::y_sweep(Real ch, TimeReal dt_time) {
    if (m_ny <= 1) return;
    const Real dt = static_cast<Real>(dt_time);
    auto gv = m_grid.view();
    const int nx = gv.nx, ny = gv.ny;
    // step() re-applies BCs before calling y_sweep, so the y-ghost cells are
    // valid (periodic wrap / outflow + psi=0). Rotate each y-stencil into the
    // x-frame with mhd_swap_xy, reuse the x-direction predictor + HLL, then
    // rotate the flux back.
    for (int i = 0; i < nx; ++i) {
        std::vector<Vec<Real, MhdNVars>> flux(static_cast<std::size_t>(ny + 1));
        for (int jf = 0; jf <= ny; ++jf) {
            const int jL = jf - 1, jR = jf;
            Vec<Real, MhdNVars> lcl{}, lcr{}, rcl{}, rcr{};
            predict_faces(mhd_swap_xy(load_cell(gv, i, jL - 1)), mhd_swap_xy(load_cell(gv, i, jL)),
                          mhd_swap_xy(load_cell(gv, i, jL + 1)), dt, m_gamma, ch, m_dy, lcl, lcr);
            predict_faces(mhd_swap_xy(load_cell(gv, i, jR - 1)), mhd_swap_xy(load_cell(gv, i, jR)),
                          mhd_swap_xy(load_cell(gv, i, jR + 1)), dt, m_gamma, ch, m_dy, rcl, rcr);
            flux[static_cast<std::size_t>(jf)] =
                mhd_swap_xy(mhd_hll_flux(lcr, rcl, m_gamma, ch));  // rotate flux back
        }
        const Real dtdy = dt / m_dy;
        for (int j = 0; j < ny; ++j) {
            Vec<Real, MhdNVars> U = load_cell(gv, i, j);
            const auto& fL = flux[static_cast<std::size_t>(j)];
            const auto& fR = flux[static_cast<std::size_t>(j + 1)];
            for (int k = 0; k < MhdNVars; ++k) U[k] -= dtdy * (fR[k] - fL[k]);
            store_cell(gv, i, j, U);
        }
    }
}

template <typename Real>
void MhdSolver<Real>::step() {
    apply_bc();
    const Real ch = compute_ch();
    const TimeReal dt_time = compute_dt(ch);
    if (dt_time <= TimeReal(0)) return;
    x_sweep(ch, dt_time);
    if (m_ny > 1) {
        apply_bc();                       // refresh y-ghosts after the x-sweep
        y_sweep(ch, dt_time);
    }
    auto gv = m_grid.view();
    glm_damp<Real>(gv, gv.nx, gv.ny, ch, m_glm_cr, static_cast<Real>(dt_time));
    validate_physical_grid(gv, m_gamma);
    m_time += dt_time;
    m_step++;
}

template <typename Real>
void MhdSolver<Real>::run() {
    while (m_time < m_t_end) {
        const TimeReal old_time = m_time;
        step();
        if (!(m_time > old_time)) {
            throw std::runtime_error("MhdSolver step did not advance time");
        }
    }
}

template void setup_brio_wu<float>(GridView<float, MhdNVars>, int, float, float, float, float);
template void setup_brio_wu<double>(GridView<double, MhdNVars>, int, double, double, double, double);

template <typename Real>
void setup_brio_wu_row(GridView<Real, MhdNVars> gv, int nx, Real dx, Real xmin,
                       Real gamma, Real x0, int j) {
    for (int i = 0; i < nx; ++i) {
        const Real x = xmin + (Real(i) + Real(0.5)) * dx;
        MhdPrim<Real> w{};
        w.rho = (x < x0) ? Real(1) : Real(0.125);
        w.Bx = Real(0.75);
        w.By = (x < x0) ? Real(1) : Real(-1);
        w.p  = (x < x0) ? Real(1) : Real(0.1);
        store_cell(gv, i, j, prim_to_cons(w, gamma));  // vy=vz=Bz=psi=0 from {}
    }
}

template void setup_brio_wu_row<float>(GridView<float, MhdNVars>, int, float, float, float, float, int);
template void setup_brio_wu_row<double>(GridView<double, MhdNVars>, int, double, double, double, double, int);

template class MhdSolver<float>;
template class MhdSolver<double>;

} // namespace hrsc
