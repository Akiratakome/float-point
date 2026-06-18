#pragma once

#include "core/grid.hpp"
#include "mhd/mhd_state.hpp"

#include <cmath>

namespace hrsc {

template <typename Real, typename Ptr>
void glm_damp(GridViewBase<Real, MhdNVars, Ptr> gv, int nx, int ny,
              Real ch, Real cr, Real dt) {
    if (ch <= Real(0) || cr <= Real(0)) {
        return;
    }

    const Real cp2 = ch * cr;
    const Real factor = std::exp(-dt * ch * ch / cp2);
    for (int j = 0; j < ny; ++j) {
        for (int i = 0; i < nx; ++i) {
            gv(i, j, MhdIdx::PSI) *= factor;
        }
    }
}

} // namespace hrsc
