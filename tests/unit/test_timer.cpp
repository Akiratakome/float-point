#include "catch.hpp"
#include "utils/timer.hpp"

#include <chrono>
#include <thread>

using namespace hrsc;

TEST_CASE("Timer measures elapsed wall-clock seconds", "[timer]") {
    Timer t;
    t.start();
    std::this_thread::sleep_for(std::chrono::milliseconds(100));
    t.stop();

    double s = t.elapsed_seconds();
    REQUIRE(s >= 0.09);
}

TEST_CASE("Timer accumulates across multiple start/stop pairs", "[timer]") {
    Timer t;
    for (int i = 0; i < 3; ++i) {
        t.start();
        std::this_thread::sleep_for(std::chrono::milliseconds(50));
        t.stop();
    }
    double s = t.elapsed_seconds();
    REQUIRE(s >= 0.13);   // 3 * 50ms = 150ms, allow slack
}

TEST_CASE("Timer stop() without prior start() is a no-op", "[timer]") {
    Timer t;
    t.stop();   // must not crash, must leave elapsed at 0
    REQUIRE(t.elapsed_seconds() == 0.0);
}

#ifdef HRSC_ENABLE_PROFILING
TEST_CASE("ProfilingRegistry add() accumulates by name", "[timer][profiling]") {
    ProfilingRegistry reg;
    reg.add("phase_a", 0.10);
    reg.add("phase_a", 0.20);
    reg.add("phase_b", 0.05);

    auto snap = reg.snapshot();
    REQUIRE(snap.size() == 2);
    REQUIRE(snap["phase_a"] == Approx(0.30));
    REQUIRE(snap["phase_b"] == Approx(0.05));
}

TEST_CASE("ScopedTimer adds elapsed to its accumulator on destruction",
          "[timer][profiling]") {
    ProfilingRegistry reg;
    {
        ScopedTimer s("alpha", reg);
        std::this_thread::sleep_for(std::chrono::milliseconds(50));
    }
    auto snap = reg.snapshot();
    REQUIRE(snap.count("alpha") == 1);
    REQUIRE(snap["alpha"] >= 0.04);
}
#endif // HRSC_ENABLE_PROFILING
