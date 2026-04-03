#pragma once

#include "core/grid.hpp"

namespace hrsc {

// Outflow (transmissive) boundary conditions.
// Copies outermost physical cell values into ghost layers.
// Host-only orchestrator — no HD_FUNC on this function.
template <typename Real, int NVars>
void apply_outflow_bc(GridView<Real, NVars> grid) {
    int nx = grid.nx;
    int ny = grid.ny;
    constexpr int ng = GridView<Real, NVars>::ng;

    // --- X-boundaries ---
    // Loop over all rows including ghost rows in y, so corners get filled
    for (int j = -ng; j < ny + ng; ++j) {
        for (int var = 0; var < NVars; ++var) {
            // Clamp j to physical range for source cell
            int js = (j < 0) ? 0 : (j >= ny ? ny - 1 : j);
            for (int g = 1; g <= ng; ++g) {
                grid(-g, j, var)          = grid(0, js, var);       // left
                grid(nx - 1 + g, j, var) = grid(nx - 1, js, var); // right
            }
        }
    }

    // --- Y-boundaries ---
    // Loop over all columns including ghost columns in x (already filled above)
    for (int i = -ng; i < nx + ng; ++i) {
        for (int var = 0; var < NVars; ++var) {
            for (int g = 1; g <= ng; ++g) {
                grid(i, -g, var)          = grid(i, 0, var);        // bottom
                grid(i, ny - 1 + g, var) = grid(i, ny - 1, var);  // top
            }
        }
    }
}

} // namespace hrsc
