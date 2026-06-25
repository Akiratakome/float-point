#pragma once

#include "core/types.hpp"
#include "core/grid.hpp"
#include "core/boundary.hpp"
#include "mhd/hll.hpp"
#include "mhd/mhd_reconstruct.hpp"

namespace hrsc {

template <typename Real>
void setup_brio_wu(GridView<Real, MhdNVars> gv, int nx, Real dx, Real xmin,
                   Real gamma, Real x0);

template <typename Real>
void setup_brio_wu_row(GridView<Real, MhdNVars> gv, int nx, Real dx, Real xmin,
                       Real gamma, Real x0, int j);

template <typename Real>
void setup_divb_blob(GridView<Real, MhdNVars> gv, int nx, int ny,
                     Real dx, Real dy, Real xmin, Real ymin, Real gamma);

template <typename Real, typename RiemannFlux = HllFlux>
class MhdSolver {
    Grid2D<Real, MhdNVars> m_grid;
    Real m_xmin;
    Real m_ymin;
    Real m_dx;
    Real m_dy;
    Real m_gamma;
    Real m_cfl;
    TimeReal m_t_end;
    TimeReal m_time;
    int m_step;
    BoundaryType m_bc_x;
    int m_ny;
    BoundaryType m_bc_y;
    Real m_glm_cr;

    void apply_bc();
    Real compute_ch() const;
    void x_sweep(Real ch, TimeReal dt);
    void y_sweep(Real ch, TimeReal dt);

public:
    // 1D convenience constructor
    MhdSolver(int nx, Real dx, Real xmin, Real gamma, Real cfl, TimeReal t_end,
              BoundaryType bc_x = BoundaryType::Outflow);

    // 2D constructor
    MhdSolver(int nx, int ny, Real dx, Real dy, Real xmin, Real ymin,
              Real gamma, Real cfl, TimeReal t_end,
              BoundaryType bc_x = BoundaryType::Outflow,
              BoundaryType bc_y = BoundaryType::Outflow,
              Real glm_cr = Real(0.18));

    GridView<Real, MhdNVars> grid_view() { return m_grid.view(); }

    TimeReal time() const { return m_time; }
    int step_count() const { return m_step; }
    Real dx() const { return m_dx; }
    Real xmin() const { return m_xmin; }
    Real gamma() const { return m_gamma; }
    int ny() const { return m_ny; }
    Real glm_cr() const { return m_glm_cr; }

    TimeReal compute_dt(Real ch) const;
    void step();
    void run();
};

} // namespace hrsc
