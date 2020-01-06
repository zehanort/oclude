#include <iostream>
#include <fstream>
#include <variant>
#include <cstdlib>
#include <ctime>
#include <random>
#include "argparse.hpp"
#ifdef __APPLE__
    #include <OpenCL/cl.hpp>
#else
    #include <CL/cl.hpp>
#endif

#define EMPTY_STRING (std::string(""))

class MessagePrinter {
private:
    std::string prompt;
public:
    MessagePrinter() {
        std::string filename = std::string(__FILE__);
        std::string appname = filename.substr(0, filename.find_last_of("."));
        prompt = "[" + appname + "] ";
    }
    void operator()(std::string message, bool nl=true) {
        std::cerr << prompt << message;
        if (nl) std::cerr << std::endl;
    }
};

MessagePrinter print_message;

// buffer args
using v_int = std::vector<cl_int>;
using v_uint = std::vector<cl_uint>;
using v_float = std::vector<cl_float>;

using kernel_args_t = std::vector<std::variant<cl_int, cl_uint, cl_float, v_int, v_uint, v_float>>;

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

int main(int argc, char const *argv[]) {

    ArgumentParser parser;

    parser.addArgument("-f", "--file", 1, false);
    parser.addArgument("-k", "--kernel", 1, false);
    parser.addArgument("-s", "--size", 1, false);
    parser.addArgument("-w", "--work-groups", 1, false);
    parser.addArgument("-p", "--platform", 1);
    parser.addArgument("-d", "--device", 1);

    parser.parse(argc, argv);

    std::string kernel_file  = parser.retrieve<std::string>("file");
    std::string kernel_name  = parser.retrieve<std::string>("kernel");
    unsigned LENGTH          = (unsigned) std::stoi(parser.retrieve<std::string>("size"));
    unsigned WORK_GROUPS     = (unsigned) std::stoi(parser.retrieve<std::string>("work-groups"));
    std::string platform_str = parser.retrieve<std::string>("platform");
    std::string device_str   = parser.retrieve<std::string>("device");
    unsigned platform_id, device_id;
    std::string platform_name, device_name;

    /******************************
     * PART 1: PLATFORM SELECTION *
     ******************************/
    std::vector<cl::Platform> platforms;
    cl::Platform::get(&platforms);

    if (platform_str == EMPTY_STRING) {

        print_message("Platform not chosen. Available platforms:");

        if (platforms.size() == 0) {
            print_message("No platforms found. Check your OpenCL installation. Aborting. Good Luck.");
            exit(1);
        }

        for (uint i = 0; i < platforms.size(); i++)
            print_message('[' + i + "] " + platforms[i].getInfo<CL_PLATFORM_NAME>());

        platform_id = -1;

        while (platform_id >= platforms.size()) {
            if (platforms.size() > 1) {
                print_message("Choose a platform [0-" + std::to_string(platforms.size() - 1) + "]: ", false);
                std::cin >> platform_id;
            }
            else platform_id = 0;
            std::cin.clear();
        }

    }
    else {

        platform_id = (unsigned) std::stoi(platform_str);

        if (platforms.size() <= platform_id) {
            print_message("Can not use platform #" + std::to_string(platform_id) + " (number of platforms: "
                      + std::to_string(platforms.size()) + "). Aborting. Good luck.");
            exit(1);
        }

    }

    cl::Platform platform = platforms[platform_id];
    platform_name = platform.getInfo<CL_PLATFORM_NAME>();
    print_message("Using platform: " + platform_name);

    /****************************
     * PART 2: DEVICE SELECTION *
     ****************************/
    std::vector<cl::Device> devices;
    platform.getDevices(CL_DEVICE_TYPE_ALL, &devices);

    if (device_str == EMPTY_STRING) {

        print_message("Device not chosen. Available platforms for " + platform_name + ":");

        if (devices.size() == 0) {
            print_message("No devices found on platform " + platform_name +
                          ". Check your OpenCL installation. Aborting. Good Luck.");
            exit(1);
        }

        for (uint i = 0; i < devices.size(); i++)
            print_message("[" + std::to_string(i) + "] " + devices[i].getInfo<CL_DEVICE_NAME>());

        device_id = -1;

        while (device_id >= devices.size()) {
            if (devices.size() > 1) {
                print_message("Choose a device [0-" + std::to_string(devices.size() - 1) + "]: ", false);
                std::cin >> device_id;
            }
            else device_id = 0;
            std::cin.clear();
        }

    }
    else {

        device_id = (unsigned) std::stoi(device_str);

        if (devices.size() <= device_id) {
            print_message("Can not use device #" + std::to_string(device_id) + " (number of devices on selected platform: " +
                          std::to_string(devices.size()) + "). Aborting. Good luck.");
            exit(1);
        }

    }

    cl::Device device = devices[device_id];
    device_name = device.getInfo<CL_DEVICE_NAME>();
    print_message("Using device: " + device_name +
                  " (device OpenCL version: " + device.getInfo<CL_DEVICE_VERSION>() + ")");

    /************************************
     * PART 3: KERNEL ENVIRONMENT SETUP *
     ************************************/
    cl::Context context({device});
    cl::Program program(context, loadProgram(kernel_file), false);
    if (program.build({device}) != CL_SUCCESS) {
        print_message("Error building: " + program.getBuildInfo<CL_PROGRAM_BUILD_LOG>(device));
        exit(1);
    }
    cl::CommandQueue queue(context, device);
    auto kernel = cl::Kernel(program, kernel_name.c_str());

    /*****************************************
     * PART 4: KERNEL CREATION AND EXECUTION *
     *****************************************/

    /*** Step 1: identify kernel arguments ***/
    cl_uint nargs = kernel.getInfo<CL_KERNEL_NUM_ARGS>();
    for (cl_uint i = 0; i < nargs; i++)
        print_message("Argument " + std::to_string(i) + ": " + kernel.getArgInfo<CL_KERNEL_ARG_NAME>(i) + '\t' +
                                                   " type: " + kernel.getArgInfo<CL_KERNEL_ARG_TYPE_NAME>(i) + '\t' +
                                           " address qual: " + std::to_string(kernel.getArgInfo<CL_KERNEL_ARG_ADDRESS_QUALIFIER>(i)) + '\t' +
                                            " access qual: " + std::to_string(kernel.getArgInfo<CL_KERNEL_ARG_ACCESS_QUALIFIER>(i)));

    /*** Step 2: create an object for each kernel argument ***/
    bool is_buffer;
    kernel_args_t kernel_args;
    cl::Buffer counterBuffer;

    // an array of buffers for the kernel arguments
    cl::Buffer argumentBuffers[nargs];

    // initialization of several random generators needed to populate args
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<cl_int> int_dis(-LENGTH, LENGTH);
    std::uniform_int_distribution<cl_uint> uint_dis(0, LENGTH);
    std::uniform_real_distribution<cl_float> float_dis(-LENGTH, LENGTH);

    for (unsigned i = 0; i < nargs; i++) {
        // check type of arg
        std::string argtype(kernel.getArgInfo<CL_KERNEL_ARG_TYPE_NAME>(i));
        is_buffer = (*(argtype.end() - 2) == '*');

        // handle oclude counters in a special manner
        if (kernel.getArgInfo<CL_KERNEL_ARG_NAME>(i).rfind("ocludeHiddenCounterLocal", 0) == 0)
            kernel.setArg(i, cl::Local(sizeof(cl_uint) * 66));
        else if (kernel.getArgInfo<CL_KERNEL_ARG_NAME>(i).rfind("ocludeHiddenCounterGlobal", 0) == 0) {
            kernel_args.push_back(v_uint(66 * WORK_GROUPS));
            for (unsigned j = 0; j < 66 * WORK_GROUPS; j++)
                std::get<v_uint>(kernel_args.back())[j] = 0;
            argumentBuffers[i] = cl::Buffer(context, begin(std::get<v_uint>(kernel_args.back())), end(std::get<v_uint>(kernel_args.back())), false);
            kernel.setArg(i, argumentBuffers[i]);
        }

        else if (argtype.rfind("int", 0) == 0) {
            if (is_buffer) {
                kernel_args.push_back(v_int(LENGTH));
                for (unsigned j = 0; j < LENGTH; j++)
                    std::get<v_int>(kernel_args.back())[j] = int_dis(gen);
                // kernel.setArg(i, cl::Buffer(context, CL_MEM_READ_WRITE, sizeof(cl_int) * LENGTH, kernel_arg.data()));
                argumentBuffers[i] = cl::Buffer(context, begin(std::get<v_int>(kernel_args.back())), end(std::get<v_int>(kernel_args.back())), false);
                kernel.setArg(i, argumentBuffers[i]);
            }
            else {
                // kernel_args.push_back(int_dis(gen));
                kernel.setArg(i, int_dis(gen));
            }
        }
        else if (argtype.rfind("uint", 0) == 0) {
            if (is_buffer) {
                kernel_args.push_back(v_uint(LENGTH));
                for (unsigned j = 0; j < LENGTH; j++)
                    std::get<v_uint>(kernel_args.back())[j] = uint_dis(gen);
                // kernel.setArg(i, cl::Buffer(context, CL_MEM_READ_WRITE, sizeof(cl_uint) * LENGTH, kernel_arg.data()));
                argumentBuffers[i] = cl::Buffer(context, begin(std::get<v_uint>(kernel_args.back())), end(std::get<v_uint>(kernel_args.back())), false);
                kernel.setArg(i, argumentBuffers[i]);
            }
            else {
                // kernel_args.push_back(uint_dis(gen));
                kernel.setArg(i, uint_dis(gen));
            }
        }
        else if (argtype.rfind("float", 0) == 0) {
            if (is_buffer) {
                kernel_args.push_back(v_float(LENGTH));
                for (unsigned j = 0; j < LENGTH; j++)
                    std::get<v_float>(kernel_args.back())[j] = float_dis(gen);
                // kernel.setArg(i, cl::Buffer(context, CL_MEM_READ_WRITE, sizeof(cl_float) * LENGTH, kernel_arg.data()));
                argumentBuffers[i] = cl::Buffer(context, begin(std::get<v_float>(kernel_args.back())), end(std::get<v_float>(kernel_args.back())), false);
                kernel.setArg(i, argumentBuffers[i]);
            }
            else {
                // kernel_args.push_back(rand_float);
                kernel.setArg(i, float_dis(gen));
            }
        }
    }

    /*** Step 3: run kernel ***/
    print_message("Enqueuing kernel with Global NDRange = " + std::to_string(LENGTH) + " and Local NDRange = " + std::to_string(LENGTH / WORK_GROUPS));
    queue.enqueueNDRangeKernel(kernel, cl::NullRange, cl::NDRange(LENGTH), cl::NDRange(LENGTH / WORK_GROUPS));

    /*** Step 4: read counter buffer ***/
    v_uint globalCounter(66 * WORK_GROUPS);
    queue.enqueueReadBuffer(argumentBuffers[nargs-1], CL_TRUE, 0, sizeof(cl_uint) * 66 * WORK_GROUPS, globalCounter.data());

    /*** Step 5: aggregate instruction counts across work groups ***/
    v_uint finalCounter(66, 0);
    for (unsigned i = 0; i < 66; i++)
        for (unsigned j = 0; j < WORK_GROUPS; j++)
            finalCounter[i] += globalCounter[i + j * 66];

    /*** Step 6: report instruction counts ***/
    for (unsigned i = 0; i < finalCounter.size(); i++)
        std::cout << i << ": " << finalCounter[i] << std::endl;

    return 0;
}
