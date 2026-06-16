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
class MhdSolver {
    Grid2D<Real, MhdNVars> m_grid;
    Real m_xmin;
    Real m_dx;
    Real m_gamma;
    Real m_cfl;
    TimeReal m_t_end;
    TimeReal m_time;
    int m_step;
    BoundaryType m_bc_x;

    void apply_bc();
    Real compute_ch() const;

public:
    MhdSolver(int nx, Real dx, Real xmin, Real gamma, Real cfl, TimeReal t_end,
              BoundaryType bc_x = BoundaryType::Outflow);

    GridView<Real, MhdNVars> grid_view() { return m_grid.view(); }

    TimeReal time() const { return m_time; }
    int step_count() const { return m_step; }
    Real dx() const { return m_dx; }
    Real xmin() const { return m_xmin; }
    Real gamma() const { return m_gamma; }

    TimeReal compute_dt(Real ch) const;
    void step();
    void run();
};

} // namespace hrsc
