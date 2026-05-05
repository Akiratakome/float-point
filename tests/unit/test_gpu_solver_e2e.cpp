// tests/unit/test_gpu_solver_e2e.cpp
//
// End-to-end bit-exact regression tests for EulerGpuSolver: build a CPU
// solver and a GPU solver from the same IC, run identical steps on both,
// and require the post-step grids to be byte-identical (memcmp).
// T16 lands the 1-step Sod 1D smoke; T18 will populate the remaining cases.

#include "catch.hpp"

#ifdef HRSC_HAS_CUDA

#include "core/grid.hpp"
#include "euler/euler_solver.hpp"
#include "gpu/euler_gpu_solver.hpp"
#include "../cases/toro_1d/toro_tests.hpp"

#include <cstring>

using namespace hrsc;

namespace {

template <typename Real>
bool grid_byte_equal(const Grid2D<Real, EulerNVars>& a,
                     const Grid2D<Real, EulerNVars>& b) {
    return a.data.size() == b.data.size() &&
           std::memcmp(a.data.data(), b.data.data(),
                       a.data.size() * sizeof(Real)) == 0;
}

} // namespace

TEST_CASE("EulerGpuSolver runs 1 step on Sod 1D bit-exact to CPU",
          "[gpu][e2e]") {
    auto run = [](auto real_tag) {
        using Real = decltype(real_tag);
        const int nx = 200;
        const Real dx = Real(1) / static_cast<Real>(nx);
        const Real gamma = Real(1.4);
        const Real cfl = Real(0.5);
        const TimeReal t_end = TimeReal(0.25);

        // Build CPU solver, fill IC.
        EulerSolver<Real> cpu(nx, dx, Real(0), gamma, cfl, t_end,
                              FluxScheme::Rusanov,
                              BoundaryType::Outflow, BoundaryType::Outflow);
        setup_sod<Real>(cpu.grid_view(), gamma);

        // Build GPU solver from a host grid filled with the same IC.
        Grid2D<Real, EulerNVars> ic_grid(nx, 1);
        ic_grid.dx = dx;
        ic_grid.dy = dx;
        setup_sod<Real>(ic_grid.view(), gamma);
        EulerGpuSolver<Real> gpu(std::move(ic_grid),
                                 Real(0), Real(0), gamma, cfl, t_end,
                                 FluxScheme::Rusanov,
                                 BoundaryType::Outflow,
                                 BoundaryType::Outflow);

        // Run exactly 1 step on each. CPU::step() applies BC, computes dt
        // internally, then sweeps; GPU::step requires us to pass dt — so we
        // mirror CPU's dt by computing it from the GPU side first (bit-exact
        // because CFL reduction is deterministic on both paths).
        cpu.step();

        // Grab the GPU's first-step dt from the GPU CFL kernel directly: we
        // pass the same dt to gpu.step that CPU's compute_dt would have
        // returned. Easier: run gpu's run() with a single-step horizon.
        // Simpler still: compute CPU dt and feed gpu.step.
        const TimeReal dt_first = cpu.time();  // CPU.time() == dt after 1 step.
        gpu.step(dt_first);

        // Compare interior data (memcmp full host grid arrays).
        // CPU grid_view().data is a raw pointer over the same backing
        // buffer; copy it into a fresh Grid2D for the byte comparison.
        Grid2D<Real, EulerNVars> cpu_grid_copy(nx, 1);
        cpu_grid_copy.dx = dx;
        cpu_grid_copy.dy = dx;
        std::memcpy(cpu_grid_copy.data.data(), cpu.grid_view().data,
                    cpu_grid_copy.data.size() * sizeof(Real));

        const auto gpu_grid_copy = gpu.download_host_grid();
        REQUIRE(grid_byte_equal(cpu_grid_copy, gpu_grid_copy));
    };
    run(double{});
    run(float{});
}

#endif // HRSC_HAS_CUDA
