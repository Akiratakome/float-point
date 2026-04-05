#pragma once

#include "core/types.hpp"
#include "core/vec.hpp"
#include "core/grid.hpp"
#include "core/eos.hpp"
#include "core/boundary.hpp"
#include "euler/hancock.hpp"
#include "euler/hllc.hpp"

#include <vector>
#include <cmath>
#include <algorithm>
#include <limits>

namespace hrsc {

template <typename Real>
class EulerSolver {
    Grid2D<Real, 4> m_grid;
    Real m_gamma;
    Real m_cfl;
    Real m_t_end;
    Real m_time;
    int  m_step;

public:
    EulerSolver(int nx, Real dx, Real gamma, Real cfl, Real t_end)
        : m_grid(nx, 1),
          m_gamma(gamma),
          m_cfl(cfl),
          m_t_end(t_end),
          m_time(Real(0)),
          m_step(0)
    {
        m_grid.dx = dx;
        m_grid.dy = dx;  // dummy for 1D
    }

    GridView<Real, 4> grid_view() {
        return m_grid.view();
    }

    Real time() const { return m_time; }
    int  step_count() const { return m_step; }

    // Compute stable time step from CFL condition.
    // dt = CFL * dx / max_all(|u| + a)
    Real compute_dt() const {
        auto gv = m_grid.view();
        int nx = gv.nx;
        Real max_speed = std::numeric_limits<Real>::min();

        for (int i = 0; i < nx; ++i) {
            Vec<Real, 4> cons;
            for (int v = 0; v < 4; ++v) cons[v] = gv(i, 0, v);

            Real rho = cons[RHO];
            Real u   = cons[RHOU] / rho;
            Real p   = pressure(cons, m_gamma);
            Real a   = sound_speed(rho, p, m_gamma);

            max_speed = std::max(max_speed, std::abs(u) + a);
        }

        Real dt = m_cfl * gv.dx / max_speed;

        // Clip to reach t_end exactly
        if (m_time + dt > m_t_end) {
            dt = m_t_end - m_time;
        }

        return dt;
    }

    // Execute one time step (x-sweep only, 1D).
    void step() {
        auto gv = m_grid.view();
        int nx = gv.nx;

        // 1. Apply boundary conditions
        apply_outflow_bc(gv);

        // 2. Compute dt
        Real dt = compute_dt();
        if (dt <= Real(0)) return;

        // 3. Compute interface fluxes
        //    Interface k is between cell k-1 and cell k.
        //    We need nx+1 interfaces: k = 0 (left of cell 0) to k = nx (right of cell nx-1).
        int n_interfaces = nx + 1;
        std::vector<Vec<Real, 4>> flux(n_interfaces);

        for (int k = 0; k < n_interfaces; ++k) {
            // Interface k is between cell (k-1) and cell k.
            int iL = k - 1;  // cell to the left of interface
            int iR = k;      // cell to the right of interface

            Vec<Real, 4> qL_left{}, qL_right{};
            Vec<Real, 4> qR_left{}, qR_right{};

            muscl_hancock_x(gv, iL, 0, dt, m_gamma, qL_left, qL_right);
            muscl_hancock_x(gv, iR, 0, dt, m_gamma, qR_left, qR_right);

            // At interface k: use right face of left cell, left face of right cell
            flux[k] = hllc_flux(qL_right, qR_left, m_gamma);
        }

        // 4. Conservative update: U_i -= (dt/dx) * (flux[i+1] - flux[i])
        Real dtdx = dt / gv.dx;
        for (int i = 0; i < nx; ++i) {
            for (int v = 0; v < 4; ++v) {
                gv(i, 0, v) -= dtdx * (flux[i + 1][v] - flux[i][v]);
            }
        }

        // 5. Advance time
        m_time += dt;
        m_step++;
    }

    // Run until t >= t_end.
    void run() {
        while (m_time < m_t_end) {
            step();
        }
    }
};

} // namespace hrsc
