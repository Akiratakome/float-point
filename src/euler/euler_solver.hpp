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

#ifdef HRSC_ENABLE_PROFILING
#include "utils/timer.hpp"
#endif

#include <array>
#include <vector>
#include <cmath>
#include <algorithm>
#include <limits>
#include <chrono>
#include <cstdio>

namespace hrsc {

enum class FluxScheme { HLLC, Rusanov };

namespace detail {
    // ETA estimator becomes unreliable when the simulation has barely begun
    // (t / t_end too small): print "0.0s" rather than a meaningless huge number.
    constexpr double kProgressEtaMinFrac = 1e-12;
    // Wall-clock granularity floor for the per-tick rate estimate; below this
    // the steps/s computation underflows or produces nonsense due to clock noise.
    constexpr double kProgressMinIntervalSeconds = 1e-9;
}

// EulerSolver class: declaration only. Long method bodies (ctor, sweeps,
// compute_dt, step, run) live in euler_solver.cpp with explicit instantiation
// for float and double at the bottom. Free function templates such as
// hllc_flux/rusanov_flux/muscl_hancock_* remain header-only because unit tests
// instantiate them directly and small inline functions are kept in the header
// for future GPU kernel reuse.
template <typename Real>
class EulerSolver {
    Grid2D<Real, EulerNVars> m_grid;
    Real m_xmin;
    Real m_ymin;
    Real m_gamma;
    Real m_cfl;
    // Time accumulator is TimeReal=double regardless of Real -- see
    // src/core/types.hpp for the rationale (avoids float32 clock stall
    // for long evolutions, decouples state precision from clock precision).
    TimeReal m_t_end;
    TimeReal m_time;
    TimeReal m_kahan_c;  // Kahan compensated-summation running correction
    int  m_step;
    FluxScheme m_flux;
    BoundaryType m_bc_x;
    BoundaryType m_bc_y;

    void apply_boundary_conditions();
    void x_sweep(TimeReal dt);
    void y_sweep(TimeReal dt);

#ifdef HRSC_ENABLE_PROFILING
public:
    ProfilingRegistry& profiling() { return m_prof_; }
    const ProfilingRegistry& profiling() const { return m_prof_; }
private:
    mutable ProfilingRegistry m_prof_;
#endif

public:
    // 2D constructor
    EulerSolver(int nx, int ny, Real dx, Real dy,
                Real xmin, Real ymin,
                Real gamma, Real cfl, TimeReal t_end,
                FluxScheme flux = FluxScheme::HLLC,
                BoundaryType bc_x = BoundaryType::Outflow,
                BoundaryType bc_y = BoundaryType::Outflow);

    // 1D convenience constructor
    EulerSolver(int nx, Real dx, Real xmin, Real gamma, Real cfl, TimeReal t_end,
                FluxScheme flux = FluxScheme::HLLC,
                BoundaryType bc_x = BoundaryType::Outflow,
                BoundaryType bc_y = BoundaryType::Outflow);

    GridView<Real, EulerNVars> grid_view() {
        return m_grid.view();
    }

    TimeReal time()       const { return m_time; }
    int      step_count() const { return m_step; }
    Real     xmin()       const { return m_xmin; }
    Real     ymin()       const { return m_ymin; }

    TimeReal compute_dt() const;
    void step();
    void run();

    // Run with a wall-clock-throttled progress line on stderr.
    // progress_interval_s <= 0 disables printing (equivalent to run()).
    void run(double progress_interval_s);
};

} // namespace hrsc
