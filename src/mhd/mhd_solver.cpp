#include "mhd/mhd_solver.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <limits>
#include <vector>

namespace hrsc {

namespace {

template <typename Real, typename Ptr>
Vec<Real, MhdNVars> load_cell(GridViewBase<Real, MhdNVars, Ptr> gv, int i) {
    Vec<Real, MhdNVars> U{};
    for (int k = 0; k < MhdNVars; ++k) {
        U[k] = gv(i, 0, k);
    }
    return U;
}

template <typename Real>
void store_cell(GridView<Real, MhdNVars> gv, int i, const Vec<Real, MhdNVars>& U) {
    for (int k = 0; k < MhdNVars; ++k) {
        gv(i, 0, k) = U[k];
    }
}

template <typename Real>
void predict_faces(GridView<Real, MhdNVars> gv, int i, Real dt, Real gamma,
                   Real ch, Vec<Real, MhdNVars>& left,
                   Vec<Real, MhdNVars>& right) {
    const Vec<Real, MhdNVars> Um = load_cell(gv, i - 1);
    const Vec<Real, MhdNVars> U0 = load_cell(gv, i);
    const Vec<Real, MhdNVars> Up = load_cell(gv, i + 1);
    const Vec<Real, MhdNVars> slope = mhd_slope(Um, U0, Up);

    left = U0 - Real(0.5) * slope;
    right = U0 + Real(0.5) * slope;

    const Vec<Real, MhdNVars> FL = mhd_flux_x(left, gamma, ch);
    const Vec<Real, MhdNVars> FR = mhd_flux_x(right, gamma, ch);
    const Real half_dtdx = Real(0.5) * dt / gv.dx;

    for (int k = 0; k < MhdNVars; ++k) {
        const Real predictor = half_dtdx * (FR[k] - FL[k]);
        left[k] -= predictor;
        right[k] -= predictor;
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
        store_cell(gv, i, prim_to_cons(w, gamma));
    }
}

template <typename Real>
MhdSolver<Real>::MhdSolver(int nx, Real dx, Real xmin, Real gamma, Real cfl,
                           TimeReal t_end, BoundaryType bc_x)
    : m_grid(nx, 1),
      m_xmin(xmin),
      m_dx(dx),
      m_gamma(gamma),
      m_cfl(cfl),
      m_t_end(t_end),
      m_time(TimeReal(0)),
      m_step(0),
      m_bc_x(bc_x) {
    m_grid.dx = dx;
    m_grid.dy = dx;
}

template <typename Real>
void MhdSolver<Real>::apply_bc() {
    auto gv = m_grid.view();
    static constexpr std::array<int, 2> kFlipX = {MhdIdx::MX, MhdIdx::BX};

    switch (m_bc_x) {
        case BoundaryType::Outflow:
            apply_outflow_bc(gv, Axis::X);
            break;
        case BoundaryType::Periodic:
            apply_periodic_bc(gv, Axis::X);
            break;
        case BoundaryType::Reflective:
            apply_reflective_bc(gv, Axis::X, kFlipX);
            break;
    }
}

template <typename Real>
Real MhdSolver<Real>::compute_ch() const {
    auto gv = m_grid.view();
    Real ch = Real(0);
    for (int i = 0; i < gv.nx; ++i) {
        const Vec<Real, MhdNVars> U = load_cell(gv, i);
        const MhdPrim<Real> w = cons_to_prim(U, m_gamma);
        ch = std::max(ch, std::abs(w.vx) + fast_speed_x(w, m_gamma));
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
void MhdSolver<Real>::step() {
    apply_bc();

    const Real ch = compute_ch();
    const TimeReal dt_time = compute_dt(ch);
    if (dt_time <= TimeReal(0)) {
        return;
    }

    const Real dt = static_cast<Real>(dt_time);
    auto gv = m_grid.view();
    const int nx = gv.nx;
    std::vector<Vec<Real, MhdNVars>> flux(static_cast<std::size_t>(nx + 1));

    for (int iface = 0; iface <= nx; ++iface) {
        const int iL = iface - 1;
        const int iR = iface;

        Vec<Real, MhdNVars> left_cell_left{}, left_cell_right{};
        Vec<Real, MhdNVars> right_cell_left{}, right_cell_right{};
        predict_faces(gv, iL, dt, m_gamma, ch, left_cell_left, left_cell_right);
        predict_faces(gv, iR, dt, m_gamma, ch, right_cell_left, right_cell_right);

        flux[static_cast<std::size_t>(iface)] =
            mhd_hll_flux(left_cell_right, right_cell_left, m_gamma, ch);
    }

    const Real dtdx = dt / m_dx;
    for (int i = 0; i < nx; ++i) {
        Vec<Real, MhdNVars> U = load_cell(gv, i);
        const auto& fL = flux[static_cast<std::size_t>(i)];
        const auto& fR = flux[static_cast<std::size_t>(i + 1)];
        for (int k = 0; k < MhdNVars; ++k) {
            U[k] -= dtdx * (fR[k] - fL[k]);
        }
        store_cell(gv, i, U);
    }

    m_time += dt_time;
    m_step++;
}

template <typename Real>
void MhdSolver<Real>::run() {
    while (m_time < m_t_end) {
        step();
    }
}

template void setup_brio_wu<float>(GridView<float, MhdNVars>, int, float, float, float, float);
template void setup_brio_wu<double>(GridView<double, MhdNVars>, int, double, double, double, double);

template class MhdSolver<float>;
template class MhdSolver<double>;

} // namespace hrsc
