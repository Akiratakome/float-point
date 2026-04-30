// src/gpu/cuda_utils.cuh
//
// CUDA error checking and a move-only RAII wrapper around cudaMalloc/cudaFree.

#pragma once

#include <cuda_runtime.h>

#include <cstddef>
#include <stdexcept>
#include <string>
#include <utility>

namespace hrsc {

#define HRSC_CUDA_CHECK(call)                                                \
    do {                                                                     \
        cudaError_t err__ = (call);                                          \
        if (err__ != cudaSuccess) {                                          \
            throw std::runtime_error(                                        \
                std::string("CUDA error: ") + cudaGetErrorString(err__) +   \
                " at " __FILE__ ":" + std::to_string(__LINE__));           \
        }                                                                    \
    } while (0)

template <typename T>
class DeviceArray {
public:
    DeviceArray() noexcept : ptr_(nullptr), size_(0) {}

    explicit DeviceArray(std::size_t n) : ptr_(nullptr), size_(0) {
        if (n > 0) {
            HRSC_CUDA_CHECK(cudaMalloc(reinterpret_cast<void**>(&ptr_),
                                       n * sizeof(T)));
            size_ = n;
        }
    }

    ~DeviceArray() noexcept { reset(); }

    DeviceArray(const DeviceArray&) = delete;
    DeviceArray& operator=(const DeviceArray&) = delete;

    DeviceArray(DeviceArray&& other) noexcept
        : ptr_(std::exchange(other.ptr_, nullptr)),
          size_(std::exchange(other.size_, std::size_t{0})) {}

    DeviceArray& operator=(DeviceArray&& other) noexcept {
        if (this != &other) {
            reset();
            ptr_ = std::exchange(other.ptr_, nullptr);
            size_ = std::exchange(other.size_, std::size_t{0});
        }
        return *this;
    }

    void copy_from_host(const T* host, std::size_t n) {
        if (n == 0) return;
        if (n > size_) {
            throw std::runtime_error("DeviceArray::copy_from_host overflow");
        }
        HRSC_CUDA_CHECK(cudaMemcpy(ptr_, host, n * sizeof(T),
                                   cudaMemcpyHostToDevice));
    }

    void copy_to_host(T* host, std::size_t n) const {
        if (n == 0) return;
        if (n > size_) {
            throw std::runtime_error("DeviceArray::copy_to_host overflow");
        }
        HRSC_CUDA_CHECK(cudaMemcpy(host, ptr_, n * sizeof(T),
                                   cudaMemcpyDeviceToHost));
    }

    T* data() noexcept { return ptr_; }
    const T* data() const noexcept { return ptr_; }
    std::size_t size() const noexcept { return size_; }

private:
    void reset() noexcept {
        if (ptr_ != nullptr) {
            (void)cudaFree(ptr_);
            ptr_ = nullptr;
            size_ = 0;
        }
    }

    T* ptr_;
    std::size_t size_;
};

} // namespace hrsc
