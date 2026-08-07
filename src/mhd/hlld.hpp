#pragma once

#include "mhd/hll.hpp"  // mhd_flux_x, mhd_hll_flux, cons_to_prim, fast_speed_x

#include <algorithm>
#include <cmath>
#include <limits>

namespace hrsc {

// Optional instrumentation of the HLLD decision structure. Report 2 argues that
// exposure to an implementation detail follows from how many internal decisions
// can be reached; these counters measure that instead of inferring it. The
// <= / < variants can differ only where a tie quantity is exactly zero, so the
// tie_* fields count exactly the interfaces at which the branch rule is live.
// Host-only, opt-in at compile time (HRSC_HLLD_COUNTERS) so the default binary
// and its recorded timings are unchanged; not thread-safe, which is sound
// because the MHD sweeps carry no work-sharing directives.
// The line_* fields are solver-level rather than HLLD-level: they count the
// per-line first-order HLL recomputation that the positivity guard triggers,
// which is a different mechanism from HLLD's own degenerate-state fallback and
// is the one that decides whether a completed run is describing the selected
// solver alone or the solver together with its fallback policy.
struct MhdDecisionCounters {
    unsigned long long calls = 0;
    unsigned long long fallback = 0;
    unsigned long long star_left = 0;
    unsigned long long star_right = 0;
    unsigned long long dstar_left = 0;
    unsigned long long dstar_right = 0;
    unsigned long long tie_ssl = 0;
    unsigned long long tie_ssr = 0;
    unsigned long long tie_sm = 0;
    unsigned long long line_total_x = 0;
    unsigned long long line_total_y = 0;
    unsigned long long line_revert_x = 0;
    unsigned long long line_revert_y = 0;
};

inline MhdDecisionCounters& hlld_counters() {
    static MhdDecisionCounters counters;
    return counters;
}

#if defined(HRSC_HLLD_COUNTERS) && !defined(__CUDA_ARCH__)
#define HRSC_HLLD_COUNT(field) (++::hrsc::hlld_counters().field)
#else
#define HRSC_HLLD_COUNT(field) ((void)0)
#endif

// HLLD 5-wave Riemann solver (Miyoshi & Kusano 2005) for GLM-MHD.
// The (Bx, psi) GLM pair is decoupled and solved exactly (Dedner/Mignone):
//   Bx*  = 0.5*(BxL+BxR) - 0.5*(psiR-psiL)/ch
//   psi* = 0.5*(psiL+psiR) - 0.5*ch*(BxR-BxL)
// giving F[BX]=psi*, F[PSI]=ch^2*Bx*; the 5-wave fan is evaluated on
// primitive-equivalent states rebuilt with Bn=Bx* and psi=0. Degenerate
// intermediate states fall back to HLL on that same non-GLM subsystem state.
template <typename Real>
HD_FUNC Vec<Real, MhdNVars> mhd_hlld_flux(const Vec<Real, MhdNVars>& UL,
                                          const Vec<Real, MhdNVars>& UR,
                                          Real gamma, Real ch) {
    // The GLM (Bx,psi) split below divides by ch; a non-positive or non-finite
    // ch (degenerate input / unit tests) makes it undefined -> fall back to the
    // robust HLL flux (HLL is GLM-consistent via its +-ch wave-speed clamp and
    // is well defined at ch=0).
    const Real eps = std::numeric_limits<Real>::epsilon();
    if (!(ch > eps) || !std::isfinite(ch))
        return mhd_hll_flux(UL, UR, gamma, ch);

    const Real Bxs  = Real(0.5) * (UL[MhdIdx::BX] + UR[MhdIdx::BX])
                    - Real(0.5) * (UR[MhdIdx::PSI] - UL[MhdIdx::PSI]) / ch;
    const Real psis = Real(0.5) * (UL[MhdIdx::PSI] + UR[MhdIdx::PSI])
                    - Real(0.5) * ch * (UR[MhdIdx::BX] - UL[MhdIdx::BX]);
    const Real Bn = Bxs;
    if (!std::isfinite(Bn) || !std::isfinite(psis))
        return mhd_hll_flux(UL, UR, gamma, ch);

    MhdPrim<Real> wl = cons_to_prim(UL, gamma);
    MhdPrim<Real> wr = cons_to_prim(UR, gamma);
    wl.Bx = Bn;
    wr.Bx = Bn;
    wl.psi = Real(0);
    wr.psi = Real(0);
    const Vec<Real, MhdNVars> ULf = prim_to_cons(wl, gamma);
    const Vec<Real, MhdNVars> URf = prim_to_cons(wr, gamma);

    const Real cfL = fast_speed_x(wl, gamma);
    const Real cfR = fast_speed_x(wr, gamma);
    const Real SL = std::min(wl.vx - cfL, wr.vx - cfR);
    const Real SR = std::max(wr.vx + cfR, wl.vx + cfL);
    const Real guard_factor = Real(64);  // Tolerance multiplier for near-zero fan denominators.

    auto finite_vec = [](const Vec<Real, MhdNVars>& U) {
        for (int k = 0; k < MhdNVars; ++k)
            if (!std::isfinite(U[k])) return false;
        return true;
    };

    auto finite_positive = [](Real x) {
        return std::isfinite(x) && x > Real(0);
    };

    auto with_glm = [&](Vec<Real, MhdNVars> F) {
        F[MhdIdx::BX] = psis;
        F[MhdIdx::PSI] = ch * ch * Bxs;
        return F;
    };

    auto fallback = [&]() {
        HRSC_HLLD_COUNT(fallback);
        return with_glm(mhd_hll_flux(ULf, URf, gamma, ch));
    };
    HRSC_HLLD_COUNT(calls);

    if (!std::isfinite(cfL) || !std::isfinite(cfR) ||
        !std::isfinite(SL) || !std::isfinite(SR))
        return fallback();

#ifdef RIEMANN_STRICT_INEQUALITY
    if (SL > Real(0)) return with_glm(mhd_flux_x(ULf, gamma, ch));
    if (SR < Real(0)) return with_glm(mhd_flux_x(URf, gamma, ch));
#else
    if (SL >= Real(0)) return with_glm(mhd_flux_x(ULf, gamma, ch));
    if (SR <= Real(0)) return with_glm(mhd_flux_x(URf, gamma, ch));
#endif

    const Real rhoL = wl.rho, rhoR = wr.rho;
    const Real EL = ULf[MhdIdx::E], ER = URf[MhdIdx::E];
    const Real ptL = wl.p + Real(0.5) * (Bn*Bn + wl.By*wl.By + wl.Bz*wl.Bz);
    const Real ptR = wr.p + Real(0.5) * (Bn*Bn + wr.By*wr.By + wr.Bz*wr.Bz);
    const Real mL = SL - wl.vx, mR = SR - wr.vx;
    const Real denomSM = mR*rhoR - mL*rhoL;
    const Real denomSM_scale = std::max(Real(1), std::abs(mR*rhoR) + std::abs(mL*rhoL));
    if (!(std::isfinite(denomSM) &&
          std::abs(denomSM) > eps * guard_factor * denomSM_scale))
        return fallback();
    const Real SM = (mR*rhoR*wr.vx - mL*rhoL*wl.vx - ptR + ptL) / denomSM;
    const Real pts = (mR*rhoR*ptL - mL*rhoL*ptR
                      + rhoL*rhoR*mR*mL*(wr.vx - wl.vx)) / denomSM;
    if (!std::isfinite(SM) || !std::isfinite(pts))
        return fallback();

    // Build one single-star state; returns false on a degenerate denominator.
    auto build_star = [&](const MhdPrim<Real>& w, Real Ek, Real ptk, Real Sk,
                          Real& rhos, Vec<Real, MhdNVars>& Us) -> bool {
        const Real m = Sk - w.vx;
        const Real wave_gap = Sk - SM;
        const Real gap_scale = std::max(Real(1), std::abs(Sk) + std::abs(SM));
        if (!(std::isfinite(m) && std::isfinite(wave_gap) &&
              std::abs(wave_gap) > eps * guard_factor * gap_scale))
            return false;

        rhos = w.rho * m / wave_gap;
        if (!finite_positive(rhos))
            return false;

        const Real denom = w.rho * m * (Sk - SM) - Bn*Bn;
        const Real scale = std::max(Real(1), w.rho * m * m + Bn*Bn);
        if (!(std::isfinite(denom) && std::abs(denom) > eps * guard_factor * scale))
            return false;
        const Real fac = Bn * (SM - w.vx) / denom;
        const Real vys = w.vy - w.By * fac;
        const Real vzs = w.vz - w.Bz * fac;
        const Real coef = (w.rho * m * m - Bn*Bn) / denom;
        const Real Bys = w.By * coef;
        const Real Bzs = w.Bz * coef;
        const Real vdotB  = w.vx*Bn + w.vy*w.By + w.vz*w.Bz;
        const Real vsdotBs = SM*Bn + vys*Bys + vzs*Bzs;
        const Real Es = (m*Ek - ptk*w.vx + pts*SM + Bn*(vdotB - vsdotBs)) / (Sk - SM);
        Us[MhdIdx::RHO] = rhos;   Us[MhdIdx::MX] = rhos*SM;
        Us[MhdIdx::MY]  = rhos*vys; Us[MhdIdx::MZ] = rhos*vzs;
        Us[MhdIdx::BX]  = Bn;     Us[MhdIdx::BY] = Bys; Us[MhdIdx::BZ] = Bzs;
        Us[MhdIdx::E]   = Es;     Us[MhdIdx::PSI] = Real(0);
        return finite_vec(Us);
    };

    Real rhosL = Real(0), rhosR = Real(0);
    Vec<Real, MhdNVars> UsL{}, UsR{};
    if (!build_star(wl, EL, ptL, SL, rhosL, UsL) ||
        !build_star(wr, ER, ptR, SR, rhosR, UsR))
        return fallback();  // degenerate -> HLL on the same GLM-split fan state

    if (!finite_positive(rhosL) || !finite_positive(rhosR))
        return fallback();

    const Vec<Real, MhdNVars> FL = mhd_flux_x(ULf, gamma, ch);
    const Vec<Real, MhdNVars> FR = mhd_flux_x(URf, gamma, ch);
    const Real SsL = SM - std::abs(Bn) / std::sqrt(rhosL);
    const Real SsR = SM + std::abs(Bn) / std::sqrt(rhosR);
    if (!std::isfinite(SsL) || !std::isfinite(SsR))
        return fallback();

    Vec<Real, MhdNVars> F;
    // RIEMANN_STRICT_INEQUALITY also flips tie ownership at the interior
    // waves (SsL/SsR/SM == 0), mirroring the HLLC S* convention (overall.md:
    // the flag controls <= vs < in HLLC/HLLD). The flux is value-continuous
    // across each tie, so the variants can differ only where FP rounding
    // decides the side.
#ifdef RIEMANN_STRICT_INEQUALITY
    const bool pick_star_left  = SsL > Real(0);
    const bool pick_star_right = SsR < Real(0);
#else
    const bool pick_star_left  = SsL >= Real(0);
    const bool pick_star_right = SsR <= Real(0);
#endif
    // Exact zeros are the only states at which <= and < can disagree, so they
    // are counted separately from the branch each rule then selects.
    if (SsL == Real(0)) HRSC_HLLD_COUNT(tie_ssl);
    if (SsR == Real(0)) HRSC_HLLD_COUNT(tie_ssr);
    if (SM  == Real(0)) HRSC_HLLD_COUNT(tie_sm);
    if (pick_star_left) {
        HRSC_HLLD_COUNT(star_left);
        F = FL + SL * (UsL - ULf);                      // F*L
    } else if (pick_star_right) {
        HRSC_HLLD_COUNT(star_right);
        F = FR + SR * (UsR - URf);                      // F*R
    } else {
        // Double-star region: combine the two single-star states across the
        // rotational (Alfven) waves, contact at SM.
        const Real sgn = (Bn >= Real(0)) ? Real(1) : Real(-1);
        const Real sqL = std::sqrt(rhosL), sqR = std::sqrt(rhosR);
        const Real inv = Real(1) / (sqL + sqR);
        if (!(std::isfinite(sqL) && std::isfinite(sqR) && std::isfinite(inv)))
            return fallback();

        const Real vyL = UsL[MhdIdx::MY]/rhosL, vzL = UsL[MhdIdx::MZ]/rhosL;
        const Real vyR = UsR[MhdIdx::MY]/rhosR, vzR = UsR[MhdIdx::MZ]/rhosR;
        const Real ByL = UsL[MhdIdx::BY], BzL = UsL[MhdIdx::BZ];
        const Real ByR = UsR[MhdIdx::BY], BzR = UsR[MhdIdx::BZ];
        const Real vyss = (sqL*vyL + sqR*vyR + (ByR - ByL)*sgn) * inv;
        const Real vzss = (sqL*vzL + sqR*vzR + (BzR - BzL)*sgn) * inv;
        const Real Byss = (sqL*ByR + sqR*ByL + sqL*sqR*(vyR - vyL)*sgn) * inv;
        const Real Bzss = (sqL*BzR + sqR*BzL + sqL*sqR*(vzR - vzL)*sgn) * inv;
        const Real vssdotBss = SM*Bn + vyss*Byss + vzss*Bzss;

        auto build_dstar = [&](Real rhos, const Vec<Real, MhdNVars>& Us,
                               Real vy, Real vz, Real By, Real Bz, Real sq, Real sign,
                               Vec<Real, MhdNVars>& Uss) {
            Uss = Us;
            Uss[MhdIdx::MX] = rhos*SM; Uss[MhdIdx::MY] = rhos*vyss; Uss[MhdIdx::MZ] = rhos*vzss;
            Uss[MhdIdx::BY] = Byss; Uss[MhdIdx::BZ] = Bzss;
            const Real vsdotBs = SM*Bn + vy*By + vz*Bz;
            Uss[MhdIdx::E] = Us[MhdIdx::E] + sign * sq * (vsdotBs - vssdotBss);
            return finite_vec(Uss);
        };
        Vec<Real, MhdNVars> UssL{}, UssR{};
        if (!build_dstar(rhosL, UsL, vyL, vzL, ByL, BzL, sqL, -sgn, UssL) ||
            !build_dstar(rhosR, UsR, vyR, vzR, ByR, BzR, sqR, +sgn, UssR))
            return fallback();

#ifdef RIEMANN_STRICT_INEQUALITY
        const bool pick_dstar_left = SM > Real(0);
#else
        const bool pick_dstar_left = SM >= Real(0);
#endif
        if (pick_dstar_left) {
            HRSC_HLLD_COUNT(dstar_left);
            F = FL + SsL * UssL - (SsL - SL) * UsL - SL * ULf;  // F**L
        } else {
            HRSC_HLLD_COUNT(dstar_right);
            F = FR + SsR * UssR - (SsR - SR) * UsR - SR * URf;  // F**R
        }
    }
    if (!finite_vec(F))
        return fallback();
    return with_glm(F);
}

// Functor wrapper (mirrors HllFlux) so MhdSolver can select HLLD.
struct HlldFlux {
    template <typename Real>
    HD_FUNC Vec<Real, MhdNVars> operator()(const Vec<Real, MhdNVars>& UL,
                                           const Vec<Real, MhdNVars>& UR,
                                           Real gamma, Real ch) const {
        return mhd_hlld_flux(UL, UR, gamma, ch);
    }
};

} // namespace hrsc
