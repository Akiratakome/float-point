#pragma once

#include "core/grid.hpp"
#include "core/eos.hpp"

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

// Periodic boundary conditions.
// Ghost cells copy from the opposite physical side.
template <typename Real, int NVars>
void apply_periodic_bc(GridView<Real, NVars> grid) {
    int nx = grid.nx;
    int ny = grid.ny;
    constexpr int ng = GridView<Real, NVars>::ng;

    // --- X-boundaries ---
    for (int j = -ng; j < ny + ng; ++j) {
        int js = ((j % ny) + ny) % ny;
        for (int var = 0; var < NVars; ++var) {
            for (int g = 1; g <= ng; ++g) {
                int src_left = ((nx - g) % nx + nx) % nx;
                int src_right = ((g - 1) % nx + nx) % nx;
                grid(-g, j, var)          = grid(src_left, js, var);   // left from right
                grid(nx - 1 + g, j, var) = grid(src_right, js, var);  // right from left
            }
        }
    }

    // --- Y-boundaries ---
    for (int i = -ng; i < nx + ng; ++i) {
        for (int var = 0; var < NVars; ++var) {
            for (int g = 1; g <= ng; ++g) {
                int src_bottom = ((ny - g) % ny + ny) % ny;
                int src_top = ((g - 1) % ny + ny) % ny;
                grid(i, -g, var)          = grid(i, src_bottom, var);  // bottom from top
                grid(i, ny - 1 + g, var) = grid(i, src_top, var);     // top from bottom
            }
        }
    }
}

// Reflective boundary conditions.
// Normal momentum is sign-flipped at each boundary.
template <typename Real, int NVars>
void apply_reflective_bc(GridView<Real, NVars> grid,
                         int momentum_x_index = RHOU,
                         int momentum_y_index = RHOV) {
    int nx = grid.nx;
    int ny = grid.ny;
    constexpr int ng = GridView<Real, NVars>::ng;

    // --- X-boundaries ---
    for (int j = -ng; j < ny + ng; ++j) {
        int js = (j < 0) ? 0 : (j >= ny ? ny - 1 : j);
        for (int var = 0; var < NVars; ++var) {
            for (int g = 1; g <= ng; ++g) {
                Real left_val  = grid(g - 1, js, var);
                Real right_val = grid(nx - g, js, var);
                if (var == momentum_x_index) {
                    left_val  = -left_val;
                    right_val = -right_val;
                }
                grid(-g, j, var)          = left_val;
                grid(nx - 1 + g, j, var) = right_val;
            }
        }
    }

    // --- Y-boundaries ---
    for (int i = -ng; i < nx + ng; ++i) {
        for (int var = 0; var < NVars; ++var) {
            for (int g = 1; g <= ng; ++g) {
                Real bottom_val = grid(i, g - 1, var);
                Real top_val    = grid(i, ny - g, var);
                if (var == momentum_y_index) {
                    bottom_val = -bottom_val;
                    top_val    = -top_val;
                }
                grid(i, -g, var)          = bottom_val;
                grid(i, ny - 1 + g, var) = top_val;
            }
        }
    }
}

} // namespace hrsc
