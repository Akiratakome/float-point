#pragma once

#include "core/grid.hpp"

#include <array>
#include <cstddef>

namespace hrsc {

// Per-axis BC primitives.
//
// Rationale (week4 plan §B2/§B3): the solver must support mixed
// per-axis boundary modes (e.g. KH 2D uses bc_x=periodic, bc_y=reflective),
// so each primitive fills only the ghosts on a given axis. The dispatcher
// in EulerSolver applies the X-pass first, then the Y-pass; corner ghosts
// are filled correctly because the Y-pass reads from x-ghost columns
// already populated by the X-pass (this matches the legacy behaviour
// pinned by the "Outflow BC corner ghost cells are filled" test).
//
// Reflective uses the mirror-then-flip decomposition so MHD (Week 12)
// can pass a compile-time list of normal-flip indices (e.g. {RHOU, BX}
// for the x-axis) without bespoke overloads. An empty flip list
// degenerates to a pure mirror copy — useful for symmetric scalar fields.

enum class Axis { X, Y };
enum class BoundaryType { Outflow, Periodic, Reflective };

// Outflow (transmissive) boundary conditions on a single axis.
// Copies the outermost physical cell value into the ghost layer on that axis.
// Host-only orchestrator — no HD_FUNC on this function.
template <typename Real, int NVars>
void apply_outflow_bc(GridView<Real, NVars> grid, Axis axis) {
    int nx = grid.nx;
    int ny = grid.ny;
    constexpr int ng = GridView<Real, NVars>::ng;

    if (axis == Axis::X) {
        // Loop over all rows including ghost rows in y so the X-pass can
        // run before or after the Y-pass without missing any column.
        for (int j = -ng; j < ny + ng; ++j) {
            // Clamp j to physical range so x-pass-first ordering does not
            // depend on y-ghosts being filled yet.
            int js = (j < 0) ? 0 : (j >= ny ? ny - 1 : j);
            for (int var = 0; var < NVars; ++var) {
                for (int g = 1; g <= ng; ++g) {
                    grid(-g, j, var)         = grid(0, js, var);
                    grid(nx - 1 + g, j, var) = grid(nx - 1, js, var);
                }
            }
        }
    } else {
        // Y-pass: read the source row at i, including i in [-ng, nx+ng) so
        // corner ghosts pick up the value the X-pass already wrote.
        for (int i = -ng; i < nx + ng; ++i) {
            for (int var = 0; var < NVars; ++var) {
                for (int g = 1; g <= ng; ++g) {
                    grid(i, -g, var)         = grid(i, 0, var);
                    grid(i, ny - 1 + g, var) = grid(i, ny - 1, var);
                }
            }
        }
    }
}

// Periodic boundary conditions on a single axis.
template <typename Real, int NVars>
void apply_periodic_bc(GridView<Real, NVars> grid, Axis axis) {
    int nx = grid.nx;
    int ny = grid.ny;
    constexpr int ng = GridView<Real, NVars>::ng;

    if (axis == Axis::X) {
        for (int j = -ng; j < ny + ng; ++j) {
            int js = ((j % ny) + ny) % ny;
            for (int var = 0; var < NVars; ++var) {
                for (int g = 1; g <= ng; ++g) {
                    int src_left  = ((nx - g) % nx + nx) % nx;
                    int src_right = ((g - 1) % nx + nx) % nx;
                    grid(-g, j, var)         = grid(src_left,  js, var);
                    grid(nx - 1 + g, j, var) = grid(src_right, js, var);
                }
            }
        }
    } else {
        for (int i = -ng; i < nx + ng; ++i) {
            for (int var = 0; var < NVars; ++var) {
                for (int g = 1; g <= ng; ++g) {
                    int src_bottom = ((ny - g) % ny + ny) % ny;
                    int src_top    = ((g - 1) % ny + ny) % ny;
                    grid(i, -g, var)         = grid(i, src_bottom, var);
                    grid(i, ny - 1 + g, var) = grid(i, src_top,    var);
                }
            }
        }
    }
}

// Reflective boundary conditions on a single axis.
//
// Implemented as mirror-then-flip: first copy the mirrored physical cell
// into every ghost slot for ALL components, then negate the components
// listed in `flip_indices`. The list is a compile-time-sized std::array so
// the loop is fully unrolled and an empty array is a valid no-op flip.
//
// For Euler, callers pass `{RHOU}` for Axis::X and `{RHOV}` for Axis::Y.
// MHD (Week 12) will pass `{RHOU, BX}` and `{RHOV, BY}` respectively.
template <typename Real, int NVars, std::size_t NFlips>
void apply_reflective_bc(GridView<Real, NVars> grid, Axis axis,
                         const std::array<int, NFlips>& flip_indices) {
    int nx = grid.nx;
    int ny = grid.ny;
    constexpr int ng = GridView<Real, NVars>::ng;

    if (axis == Axis::X) {
        for (int j = -ng; j < ny + ng; ++j) {
            int js = (j < 0) ? 0 : (j >= ny ? ny - 1 : j);
            // Stage 1: mirror copy for every component.
            for (int var = 0; var < NVars; ++var) {
                for (int g = 1; g <= ng; ++g) {
                    grid(-g, j, var)         = grid(g - 1,  js, var);
                    grid(nx - 1 + g, j, var) = grid(nx - g, js, var);
                }
            }
            // Stage 2: sign-flip just the listed components.
            for (std::size_t k = 0; k < NFlips; ++k) {
                int var = flip_indices[k];
                for (int g = 1; g <= ng; ++g) {
                    grid(-g, j, var)         = -grid(-g, j, var);
                    grid(nx - 1 + g, j, var) = -grid(nx - 1 + g, j, var);
                }
            }
        }
    } else {
        for (int i = -ng; i < nx + ng; ++i) {
            // Stage 1: mirror copy for every component.
            for (int var = 0; var < NVars; ++var) {
                for (int g = 1; g <= ng; ++g) {
                    grid(i, -g, var)         = grid(i, g - 1,  var);
                    grid(i, ny - 1 + g, var) = grid(i, ny - g, var);
                }
            }
            // Stage 2: sign-flip just the listed components.
            for (std::size_t k = 0; k < NFlips; ++k) {
                int var = flip_indices[k];
                for (int g = 1; g <= ng; ++g) {
                    grid(i, -g, var)         = -grid(i, -g, var);
                    grid(i, ny - 1 + g, var) = -grid(i, ny - 1 + g, var);
                }
            }
        }
    }
}

} // namespace hrsc
