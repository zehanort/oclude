#include <iostream>
#include <fstream>
#include <cstdlib>
#include <ctime>
#include <variant>
#include <random>
#ifdef __APPLE__
    #include <OpenCL/cl.hpp>
#else
    #include <CL/cl.hpp>
#endif

#include "typegen.hpp"
#include "message-printer.hpp"

#define OCLUDE_COUNTER_LOCAL  (std::string("ocludeHiddenCounterLocal"))
#define OCLUDE_COUNTER_GLOBAL (std::string("ocludeHiddenCounterGlobal"))
#define COUNTER_BUFFER_SIZE   74

using args_t         = std::tuple<std::string, std::string, uint, uint, int, int>;
using kernel_setup_t = std::pair<cl::Kernel, cl::CommandQueue>;

MessagePrinter print_message(__FILE__, "<file> <kernel> <size> <work groups> [<platform>] [<device>]");

/* a class to export some boilerplate functionality of the OpenCL runtime to the hostcode */
class OpenCLutils {

private:

    /* variables needed by the OpenCL runtime environment */
    cl::Context context;
    cl::Program program;
    cl::CommandQueue queue;
    uint nargs = 0;                 // number of kernel arguments
    cl::Buffer counterBuffer;
    cl::Buffer *argumentBuffers;    // an array of buffers for the kernel arguments
    std::vector<void *> arguments;    

public:

    ~OpenCLutils() { for (auto x : arguments) free(x); }

    inline args_t parse_arguments(int argc, char const *argv[]) {
        std::string kernel_file = argv[1];
        std::string kernel_name = argv[2];
        uint LENGTH = std::stoi(argv[3]);
        uint WORK_GROUPS = std::stoi(argv[4]);
        int platform_idx = (argc > 5 ? std::stoi(argv[5]) : -1);
        int device_idx   = (argc > 6 ? std::stoi(argv[6]) : -1);
        return { kernel_file, kernel_name, LENGTH, WORK_GROUPS, platform_idx, device_idx };
    }

    inline auto cl_get_platform(int platform_id) {

        std::vector<cl::Platform> platforms;
        cl::Platform::get(&platforms);

        if (platform_id == -1) {

            print_message("Platform not chosen. Available platforms:");

            if (platforms.size() == 0) {
                print_message("No platforms found. Check your OpenCL installation. Aborting. Good Luck.");
                exit(1);
            }

            for (uint i = 0; i < platforms.size(); i++)
                print_message('[' + std::to_string(i) + "] " + platforms[i].getInfo<CL_PLATFORM_NAME>());

            while ((uint)platform_id >= platforms.size()) {
                if (platforms.size() > 1) {
                    print_message("Choose a platform [0-" + std::to_string(platforms.size() - 1) + "]: ", false);
                    std::cin >> platform_id;
                }
                else platform_id = 0;
                std::cin.clear();
            }

        }
        else if (platforms.size() <= (uint)platform_id) {
            print_message("Can not use platform #" + std::to_string(platform_id) + " (number of platforms: "
                      + std::to_string(platforms.size()) + "). Aborting. Good luck.");
            exit(1);
        }

        cl::Platform platform = platforms[platform_id];
        std::string platform_name = platform.getInfo<CL_PLATFORM_NAME>();
        print_message("Using platform: " + platform_name);

        return platform;

    }

    inline auto cl_get_device(cl::Platform platform, int device_id) {

        std::string platform_name = platform.getInfo<CL_PLATFORM_NAME>();
        std::vector<cl::Device> devices;
        platform.getDevices(CL_DEVICE_TYPE_ALL, &devices);

        if (device_id == -1) {

            print_message("Device not chosen. Available platforms for " + platform_name + ":");

            if (devices.size() == 0) {
                print_message("No devices found on platform " + platform_name +
                              ". Check your OpenCL installation. Aborting. Good Luck.");
                exit(1);
            }

            for (uint i = 0; i < devices.size(); i++)
                print_message("[" + std::to_string(i) + "] " + devices[i].getInfo<CL_DEVICE_NAME>());

            while ((uint)device_id >= devices.size()) {
                if (devices.size() > 1) {
                    print_message("Choose a device [0-" + std::to_string(devices.size() - 1) + "]: ", false);
                    std::cin >> device_id;
                }
                else device_id = 0;
                std::cin.clear();
            }

        }
        else if (devices.size() <= (uint)device_id) {
            print_message("Can not use device #" + std::to_string(device_id) + " (number of devices on selected platform: " +
                          std::to_string(devices.size()) + "). Aborting. Good luck.");
            exit(1);
        }

        cl::Device device = devices[device_id];
        std::string device_name = device.getInfo<CL_DEVICE_NAME>();
        print_message("Using device: " + device_name + " (device OpenCL version: " + device.getInfo<CL_DEVICE_VERSION>() + ")");

        return device;
    }

    inline std::string loadProgram(std::string input) {
        std::ifstream stream(input.c_str());
        if (!stream.is_open()) {
            print_message("Cannot open file: " + input);
            exit(1);
        }
        return std::string(
            std::istreambuf_iterator<char>(stream),
            std::istreambuf_iterator<char>()
        );
    }

    inline kernel_setup_t cl_setup_kernel(cl::Device device, std::string kernel_file, std::string kernel_name) {
        print_message("Kernel name: " + kernel_name);
        context = cl::Context({device});
        program = cl::Program(context, loadProgram(kernel_file), false);
        if (program.build({device}) != CL_SUCCESS) {
            print_message("Error building: " + program.getBuildInfo<CL_PROGRAM_BUILD_LOG>(device));
            exit(1);
        }
        queue = cl::CommandQueue(context, device);
        return { cl::Kernel(program, kernel_name.c_str()), queue };
    }

    /* for pretty-printing only */
    inline std::string resolve_address_qualifier(uint address_qual) {
        switch (address_qual) {
            case CL_KERNEL_ARG_ADDRESS_GLOBAL:   return "global";
            case CL_KERNEL_ARG_ADDRESS_CONSTANT: return "constant";
            case CL_KERNEL_ARG_ADDRESS_LOCAL:    return "local";
            default:                             return "private";
        }
    }

    inline void report_kernel_arguments(cl::Kernel kernel) {
        nargs = kernel.getInfo<CL_KERNEL_NUM_ARGS>();
        for (uint i = 0; i < nargs; i++) {
            if ((kernel.getArgInfo<CL_KERNEL_ARG_NAME>(i).rfind(OCLUDE_COUNTER_LOCAL, 0) == 0) ||
                (kernel.getArgInfo<CL_KERNEL_ARG_NAME>(i).rfind(OCLUDE_COUNTER_GLOBAL, 0) == 0))
                continue;
            print_message("Kernel arg " + std::to_string(i)
                                        + ": " + kernel.getArgInfo<CL_KERNEL_ARG_NAME>(i)
                                        + " (" + kernel.getArgInfo<CL_KERNEL_ARG_TYPE_NAME>(i)
                                        + ", " + resolve_address_qualifier(kernel.getArgInfo<CL_KERNEL_ARG_ADDRESS_QUALIFIER>(i)) + ')'
            );
        }
        return;
    }

    inline void initialize_kernel_arguments(cl::Kernel kernel, uint LENGTH, uint WORK_GROUPS) {

        if (nargs == 0) nargs = kernel.getInfo<CL_KERNEL_NUM_ARGS>();
        argumentBuffers = new cl::Buffer[nargs];

        for (uint i = 0; i < nargs; i++) {

            // check type of arg
            std::string argtype_comp = kernel.getArgInfo<CL_KERNEL_ARG_TYPE_NAME>(i);
            argtype_comp = argtype_comp.substr(0, argtype_comp.size() - 1);
            size_t pos = argtype_comp.find("*");
            auto [ argtype, is_buffer ] = pos == std::string::npos ?
                                          std::make_pair(argtype_comp, false) :
                                          std::make_pair(argtype_comp.substr(0, pos), true);

            // handle oclude counters in a special manner
            if (kernel.getArgInfo<CL_KERNEL_ARG_NAME>(i).rfind(OCLUDE_COUNTER_LOCAL, 0) == 0)
                kernel.setArg(i, cl::Local(sizeof(cl_uint) * COUNTER_BUFFER_SIZE));

            else if (kernel.getArgInfo<CL_KERNEL_ARG_NAME>(i).rfind(OCLUDE_COUNTER_GLOBAL, 0) == 0) {
                std::vector<cl_uint> globalBuffer(COUNTER_BUFFER_SIZE * WORK_GROUPS, 0);
                argumentBuffers[i] = cl::Buffer(context, begin(globalBuffer), end(globalBuffer), false);
                kernel.setArg(i, argumentBuffers[i]);
            }

            // handle the real kernel arguments (NOTE: right now, these buffers can not be read back for some reason)
            else {
                size_t nmemb = is_buffer ? LENGTH : 1;
                auto [ argument, total_size ] = generate_kernel_argument(argtype, nmemb);
                arguments.push_back(argument);
                if (is_buffer) {
                    argumentBuffers[i] = cl::Buffer(context, CL_MEM_READ_WRITE, total_size, argument);
                    kernel.setArg(i, argumentBuffers[i]);
                }
                else
                    kernel.setArg(i, total_size, argument);
            }

        }
        return;
    }

    inline auto get_global_counter() { return argumentBuffers[nargs-1]; }

    inline void report_instruction_counts(auto globalCounter, uint WORK_GROUPS) {
        std::vector<uint> finalCounter(COUNTER_BUFFER_SIZE, 0);
        for (uint i = 0; i < COUNTER_BUFFER_SIZE; i++)
            for (uint j = 0; j < WORK_GROUPS; j++)
                finalCounter[i] += globalCounter[i + j * COUNTER_BUFFER_SIZE];
        for (uint i = 0; i < finalCounter.size(); i++)
            std::cout << i << ": " << finalCounter[i] << std::endl;
        return;
    }

};
