// src/utils/timer.hpp
//
// Wall-clock timing utility. Two layers:
//
//   - Timer: always available. start()/stop()/elapsed_seconds() over
//     std::chrono::steady_clock. Repeated start/stop pairs accumulate.
//
//   - ProfilingRegistry + ScopedTimer: only when HRSC_ENABLE_PROFILING is
//     defined. RAII probe that adds elapsed time to a named accumulator in
//     a registry. Default builds have HRSC_ENABLE_PROFILING undefined and
//     pay zero cost.
//
// AGENTS.md rule 1: no change to solver numerics or cfg defaults under any
// setting. Timer is wall-clock-only; never on the algorithmic path.

#pragma once

#include <chrono>

#ifdef HRSC_ENABLE_PROFILING
#include <map>
#include <ostream>
#include <string>
#include <string_view>
#endif

namespace hrsc {

class Timer {
public:
    Timer() : t0_{}, accum_s_(0.0), running_(false) {}

    void start() {
        t0_ = std::chrono::steady_clock::now();
        running_ = true;
    }

    void stop() {
        if (!running_) return;
        auto t1 = std::chrono::steady_clock::now();
        accum_s_ += std::chrono::duration<double>(t1 - t0_).count();
        running_ = false;
    }

    double elapsed_seconds() const { return accum_s_; }

private:
    std::chrono::steady_clock::time_point t0_;
    double accum_s_;
    bool running_;
};

#ifdef HRSC_ENABLE_PROFILING

class ProfilingRegistry {
public:
    void add(std::string_view name, double seconds) {
        accum_[std::string(name)] += seconds;
    }

    std::map<std::string, double> snapshot() const { return accum_; }

private:
    std::map<std::string, double> accum_;
};

class ScopedTimer {
public:
    ScopedTimer(std::string_view name, ProfilingRegistry& reg)
        : name_(name), reg_(reg),
          t0_(std::chrono::steady_clock::now()) {}

    ~ScopedTimer() {
        auto t1 = std::chrono::steady_clock::now();
        reg_.add(name_, std::chrono::duration<double>(t1 - t0_).count());
    }

    ScopedTimer(const ScopedTimer&) = delete;
    ScopedTimer& operator=(const ScopedTimer&) = delete;

private:
    std::string_view name_;
    ProfilingRegistry& reg_;
    std::chrono::steady_clock::time_point t0_;
};

inline void write_profiling_timings(std::ostream& out,
                                    const ProfilingRegistry& reg) {
    for (const auto& [phase, seconds] : reg.snapshot()) {
        out << "[timing] phase=" << phase << " seconds=" << seconds << "\n";
    }
}

#endif // HRSC_ENABLE_PROFILING

} // namespace hrsc
