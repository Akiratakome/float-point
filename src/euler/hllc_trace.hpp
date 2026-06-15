#pragma once

#include "core/types.hpp"
#include "core/vec.hpp"
#include "core/eos.hpp"
#include "euler/euler_flux.hpp"
#include "euler/hllc.hpp"

#include <filesystem>
#include <fstream>
#include <iomanip>
#include <limits>
#include <mutex>
#include <string>

namespace hrsc::hllc_trace {

struct TraceConfig {
    bool enabled = false;
    std::string path;
    long long max_records = 100000;
    int face_min = std::numeric_limits<int>::min();
    int face_max = std::numeric_limits<int>::max();
    int line_min = std::numeric_limits<int>::min();
    int line_max = std::numeric_limits<int>::max();
};

struct TraceState {
    TraceConfig config;
    std::ofstream out;
    std::mutex mutex;
    long long records = 0;
    int step = 0;
    double time = 0.0;
    double dt = 0.0;
};

inline TraceState& state()
{
    static TraceState s;
    return s;
}

inline void configure(const TraceConfig& cfg)
{
    auto& s = state();
    std::lock_guard<std::mutex> lock(s.mutex);
    if (s.out.is_open()) {
        s.out.close();
    }
    s.config = cfg;
    s.records = 0;
    if (!cfg.enabled || cfg.path.empty()) {
        s.config.enabled = false;
        return;
    }

    std::filesystem::path path(cfg.path);
    if (path.has_parent_path()) {
        std::filesystem::create_directories(path.parent_path());
    }
    s.out.open(path);
    if (!s.out) {
        s.config.enabled = false;
        return;
    }

    s.out << "step,sweep,face,line,time,dt,"
          << "rhoL,uL,vL,pL,rhoR,uR,vR,pR,"
          << "SL,SR,Sstar,Nstar,Dstar,branch,"
          << "flux_rho,flux_rhou,flux_rhov,flux_en\n";
    s.out << std::setprecision(17);
}

inline void close()
{
    auto& s = state();
    std::lock_guard<std::mutex> lock(s.mutex);
    if (s.out.is_open()) {
        s.out.flush();
        s.out.close();
    }
    s.config.enabled = false;
}

inline bool enabled()
{
    const auto& s = state();
    return s.config.enabled && s.out.is_open();
}

inline void set_context(int step, double time, double dt)
{
    auto& s = state();
    if (!enabled()) return;
    std::lock_guard<std::mutex> lock(s.mutex);
    s.step = step;
    s.time = time;
    s.dt = dt;
}

inline bool should_record(int face, int line)
{
    const auto& cfg = state().config;
    return cfg.enabled
        && face >= cfg.face_min && face <= cfg.face_max
        && line >= cfg.line_min && line <= cfg.line_max;
}

template <typename Real>
inline Vec<Real, EulerNVars> hllc_flux_traced(
    const Vec<Real, EulerNVars>& qL,
    const Vec<Real, EulerNVars>& qR,
    Real gamma,
    int face,
    int line,
    const char* sweep)
{
    if (!enabled() || !should_record(face, line)) {
        return hllc_flux(qL, qR, gamma);
    }

    const Real rhoL = qL[RHO];
    const Real uL = qL[RHOU] / rhoL;
    const Real vL = qL[RHOV] / rhoL;
    const Real pL = pressure(qL, gamma);
    const Real aL = sound_speed(rhoL, pL, gamma);

    const Real rhoR = qR[RHO];
    const Real uR = qR[RHOU] / rhoR;
    const Real vR = qR[RHOV] / rhoR;
    const Real pR = pressure(qR, gamma);
    const Real aR = sound_speed(rhoR, pR, gamma);

    const Real SL = hllc_min(uL - aL, uR - aR);
    const Real SR = hllc_max(uL + aL, uR + aR);
    const Real Nstar = pR - pL
                     + rhoL * uL * (SL - uL)
                     - rhoR * uR * (SR - uR);
    const Real Dstar = rhoL * (SL - uL) - rhoR * (SR - uR);
    const Real Sstar = Nstar / Dstar;

    const Vec<Real, EulerNVars> FL = euler_flux_x(qL, gamma);
    const Vec<Real, EulerNVars> FR = euler_flux_x(qR, gamma);

    Vec<Real, EulerNVars> flux{};
    const char* branch = "FR";
    if (SL >= Real(0)) {
        flux = FL;
        branch = "FL";
    }
#ifdef RIEMANN_STRICT_INEQUALITY
    else if (Sstar > Real(0)) {
#else
    else if (Sstar >= Real(0)) {
#endif
        const Real coeff = rhoL * (SL - uL) / (SL - Sstar);
        const Vec<Real, EulerNVars> UstarL = {
            coeff,
            coeff * Sstar,
            coeff * vL,
            coeff * (qL[EN] / rhoL
                     + (Sstar - uL) * (Sstar + pL / (rhoL * (SL - uL))))
        };
        flux = FL + (UstarL - qL) * SL;
        branch = "starL";
    }
    else if (SR >= Real(0)) {
        const Real coeff = rhoR * (SR - uR) / (SR - Sstar);
        const Vec<Real, EulerNVars> UstarR = {
            coeff,
            coeff * Sstar,
            coeff * vR,
            coeff * (qR[EN] / rhoR
                     + (Sstar - uR) * (Sstar + pR / (rhoR * (SR - uR))))
        };
        flux = FR + (UstarR - qR) * SR;
        branch = "starR";
    } else {
        flux = FR;
    }

    auto& s = state();
    std::lock_guard<std::mutex> lock(s.mutex);
    if (s.config.enabled && s.out.is_open() && s.records < s.config.max_records) {
        s.out << s.step << ',' << sweep << ',' << face << ',' << line << ','
              << s.time << ',' << s.dt << ','
              << static_cast<double>(rhoL) << ','
              << static_cast<double>(uL) << ','
              << static_cast<double>(vL) << ','
              << static_cast<double>(pL) << ','
              << static_cast<double>(rhoR) << ','
              << static_cast<double>(uR) << ','
              << static_cast<double>(vR) << ','
              << static_cast<double>(pR) << ','
              << static_cast<double>(SL) << ','
              << static_cast<double>(SR) << ','
              << static_cast<double>(Sstar) << ','
              << static_cast<double>(Nstar) << ','
              << static_cast<double>(Dstar) << ','
              << branch << ','
              << static_cast<double>(flux[RHO]) << ','
              << static_cast<double>(flux[RHOU]) << ','
              << static_cast<double>(flux[RHOV]) << ','
              << static_cast<double>(flux[EN]) << '\n';
        ++s.records;
    }
    return flux;
}

} // namespace hrsc::hllc_trace
