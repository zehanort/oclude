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

std::string prefix;

// buffer args
using v_int = std::vector<cl_int>;
using v_uint = std::vector<cl_uint>;
using v_float = std::vector<cl_float>;

using kernel_args_t = std::vector<std::variant<cl_int, cl_uint, cl_float, v_int, v_uint, v_float>>;

inline std::string loadProgram(std::string input) {
    std::ifstream stream(input.c_str());
    if (!stream.is_open()) {
        std::cerr << prefix << "Cannot open file: " << input << std::endl;
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

    std::string filename = std::string(__FILE__);
    std::string appname = filename.substr(0, filename.find_last_of("."));
    prefix = "[" + appname + "] ";

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

        std::cerr << prefix << "Platform not chosen. Available platforms:" << std::endl;

        if (platforms.size() == 0) {
            std::cerr << prefix << "No platforms found. Check your OpenCL installation. Aborting. Good Luck." << std::endl;
            exit(1);
        }

        for (uint i = 0; i < platforms.size(); i++)
            std::cerr << prefix << '[' << i << "] " << platforms[i].getInfo<CL_PLATFORM_NAME>() << std::endl;

        platform_id = -1;

        while (platform_id >= platforms.size()) {
            if (platforms.size() > 1) {
                std::cerr << prefix << "Choose a platform [0-" << platforms.size() - 1 << "]: ";
                std::cin >> platform_id;
            }
            else platform_id = 0;
            std::cin.clear();
        }

    }
    else {

        platform_id = (unsigned) std::stoi(platform_str);

        if (platforms.size() <= platform_id) {
            std::cerr << prefix << "Can not use platform #" << platform_id << " (number of platforms: "
                      << platforms.size() << "). Aborting. Good luck." << std::endl;
            exit(1);
        }

    }

    cl::Platform platform = platforms[platform_id];
    platform_name = platform.getInfo<CL_PLATFORM_NAME>();
    std::cerr << prefix << "Using platform: " << platform_name << std::endl;

    /****************************
     * PART 2: DEVICE SELECTION *
     ****************************/
    std::vector<cl::Device> devices;
    platform.getDevices(CL_DEVICE_TYPE_ALL, &devices);

    if (device_str == EMPTY_STRING) {

        std::cerr << prefix << "Device not chosen. Available platforms for " << platform_name << ":" << std::endl;

        if (devices.size() == 0) {
            std::cerr << prefix << "No devices found on platform " << platform_name
                      << ". Check your OpenCL installation. Aborting. Good Luck." << std::endl;
            exit(1);
        }

        for (uint i = 0; i < devices.size(); i++)
            std::cerr << prefix << '[' << i << "] " << devices[i].getInfo<CL_DEVICE_NAME>() << std::endl;

        device_id = -1;

        while (device_id >= devices.size()) {
            if (devices.size() > 1) {
                std::cerr << prefix << "Choose a device [0-" << devices.size() - 1 << "]: ";
                std::cin >> device_id;
            }
            else device_id = 0;
            std::cin.clear();
        }

    }
    else {

        device_id = (unsigned) std::stoi(device_str);

        if (devices.size() <= device_id) {
            std::cerr << prefix << "Can not use device #" << device_id << " (number of devices on selected platform: "
                      << devices.size() << "). Aborting. Good luck." << std::endl;
            exit(1);
        }

    }

    cl::Device device = devices[device_id];
    device_name = device.getInfo<CL_DEVICE_NAME>();
    std::cerr << prefix << "Using device: " << device_name
              << " (device OpenCL version: " << device.getInfo<CL_DEVICE_VERSION>() << ')' << std::endl;

    /************************************
     * PART 3: KERNEL ENVIRONMENT SETUP *
     ************************************/
    cl::Context context({device});
    cl::Program program(context, loadProgram(kernel_file), false);
    if (program.build({device}) != CL_SUCCESS) {
        std::cerr << prefix << "Error building: " << program.getBuildInfo<CL_PROGRAM_BUILD_LOG>(device) << std::endl;
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
        std::cerr << "Argument " << i << ": " << kernel.getArgInfo<CL_KERNEL_ARG_NAME>(i) << " type: "
                                              << kernel.getArgInfo<CL_KERNEL_ARG_TYPE_NAME>(i) << " address qual: "
                                              << kernel.getArgInfo<CL_KERNEL_ARG_ADDRESS_QUALIFIER>(i) << " access qual: "
                                              << kernel.getArgInfo<CL_KERNEL_ARG_ACCESS_QUALIFIER>(i) << " type qual: "
                                              << kernel.getArgInfo<CL_KERNEL_ARG_TYPE_QUALIFIER>(i) << std::endl;

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
        if (kernel.getArgInfo<CL_KERNEL_ARG_NAME>(i).rfind("ocludeHiddenCounterLocal", 0) == 0) {
            // cl::Buffer localCounterBuffer = cl::Buffer(context, begin(kernel_arg), end(kernel_arg), false);
            // queue.enqueueFillBuffer(localCounterBuffer, 0, 0, sizeof(cl_uint));
            // kernel.setArg(i, cl::Buffer(context, CL_MEM_READ_WRITE, sizeof(cl_uint) * 66, std::get<v_uint>(kernel_args[i]).data()));
            kernel.setArg(i, cl::Local(sizeof(cl_uint) * 66));
        }
        else if (kernel.getArgInfo<CL_KERNEL_ARG_NAME>(i).rfind("ocludeHiddenCounterGlobal", 0) == 0) {
            // v_uint kernel_arg(66 * WORK_GROUPS);
            // kernel_args.push_back(kernel_arg);
            // counterBuffer = cl::Buffer(context, CL_MEM_WRITE_ONLY, sizeof(cl_uint) * 66 * WORK_GROUPS);
            // kernel.setArg(i, counterBuffer);
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

    // std::cout << "HI 1" << std::endl;
    /*** Step 3: run kernel ***/
    std::cerr << prefix << "Enqueuing kernel with Global NDRange = " << LENGTH << " and Local NDRange = " << LENGTH / WORK_GROUPS << std::endl;
    queue.enqueueNDRangeKernel(kernel, cl::NullRange, cl::NDRange(LENGTH), cl::NDRange(LENGTH / WORK_GROUPS));
    // std::cout << "HI 2" << std::endl;

    /*** Step 4: read counter buffer ***/
    v_uint globalCounter(66 * WORK_GROUPS);
    // std::cout << "HI 3" << std::endl;
    queue.enqueueReadBuffer(argumentBuffers[nargs-1], CL_TRUE, 0, sizeof(cl_uint) * 66 * WORK_GROUPS, globalCounter.data());
    // std::cout << "HI 4" << std::endl;

    // std::cout << "===============" << std::endl;

    // for (unsigned i = 0; i < globalCounter.size(); i++)
    //     std::cout << i <<": " << globalCounter[i] << std::endl;

    // std::cout << "===============" << std::endl;

    /*** Step 5: aggregate instruction counts across work groups ***/
    v_uint finalCounter(66, 0);
    for (unsigned i = 0; i < 66; i++)
        for (unsigned j = 0; j < WORK_GROUPS; j++)
            finalCounter[i] += globalCounter[i + j * 66];

    /*** Step 6: report instruction counts ***/
    for (unsigned i = 0; i < finalCounter.size(); i++)
        std::cout << i << ": " << finalCounter[i] << std::endl;

    /*** TESTING VADD FOR NOW (WORKING EXAMPLE) ***/

    /*********************************************************************************************/
    // int LENGTH = input_size;

    // std::vector<int> h_a(LENGTH);  // a vector
    // std::vector<int> h_b(LENGTH);  // b vector
    // std::vector<int> h_c(LENGTH);  // c = a + b, from compute device

    // for(int i = 0; i < LENGTH; i++) h_a[i] = h_b[i] = 2*i;

    // cl::Buffer d_a = cl::Buffer(context, begin(h_a), end(h_a), true);
    // cl::Buffer d_b = cl::Buffer(context, begin(h_b), end(h_b), true);
    // cl::Buffer d_c = cl::Buffer(context, CL_MEM_WRITE_ONLY, sizeof(int) * LENGTH);

    // kernel.setArg(0, d_a);
    // kernel.setArg(1, d_b);
    // kernel.setArg(2, d_c);
    // kernel.setArg(3, LENGTH);

    // queue.enqueueNDRangeKernel(kernel, cl::NullRange, cl::NDRange(LENGTH), cl::NullRange);

    // queue.enqueueReadBuffer(d_c, CL_TRUE, 0, sizeof(int) * LENGTH, h_c.data());

    // for(int i = 0; i < LENGTH; i++)
    //     std::cerr << "h_a: " << h_a[i] << " h_b: " << h_b[i] << " h_c: " << h_c[i] << std::endl;
    /*********************************************************************************************/

    return 0;
}
