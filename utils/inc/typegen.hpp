#include <iostream>
#include <unordered_map>
#include <string>
#include <variant>
#include <random>
#ifdef __APPLE__
    #include <OpenCL/cl.hpp>
#else
    #include <CL/cl.hpp>
#endif

void set_limits(int size);
std::pair<void*, size_t> generate_kernel_argument(std::string typestr, size_t nmemb);
