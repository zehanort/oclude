#include <iostream>
#include <fstream>
#include "argparse.hpp"
#ifdef __APPLE__
    #include <OpenCL/cl.hpp>
#else
    #include <CL/cl.hpp>
#endif

#define EMPTY_STRING (std::string(""))

std::string prefix;

inline std::string loadProgram(std::string input) {
    std::ifstream stream(input.c_str());
    if (!stream.is_open()) {
        std::cout << prefix << "Cannot open file: " << input << std::endl;
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
    parser.addArgument("-p", "--platform", 1);
    parser.addArgument("-d", "--device", 1);

    parser.parse(argc, argv);

    std::string filename = std::string(__FILE__);
    std::string appname = filename.substr(0, filename.find_last_of("."));
    prefix = "[" + appname + "] ";

    std::string kernel_file  = parser.retrieve<std::string>("file");
    std::string kernel_name  = parser.retrieve<std::string>("kernel");
    unsigned input_size      = (unsigned) std::stoi(parser.retrieve<std::string>("size"));
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

        std::cout << prefix << "Platform not chosen. Available platforms:" << std::endl;

        if (platforms.size() == 0) {
            std::cout << prefix << "No platforms found. Check your OpenCL installation. Aborting. Good Luck." << std::endl;
            exit(1);
        }

        for (uint i = 0; i < platforms.size(); i++)
            std::cout << prefix << '[' << i << "] " << platforms[i].getInfo<CL_PLATFORM_NAME>() << std::endl;

        platform_id = -1;

        while (platform_id >= platforms.size()) {
            if (platforms.size() > 1) {
                std::cout << prefix << "Choose a platform [0-" << platforms.size() - 1 << "]: ";
                std::cin >> platform_id;
            }
            else platform_id = 0;
            std::cin.clear();
        }

    }
    else {

        platform_id = (unsigned) std::stoi(platform_str);

        if (platforms.size() <= platform_id) {
            std::cout << prefix << "Can not use platform #" << platform_id << " (number of platforms: "
                      << platforms.size() << "). Aborting. Good luck." << std::endl;
            exit(1);
        }

    }

    cl::Platform platform = platforms[platform_id];
    platform_name = platform.getInfo<CL_PLATFORM_NAME>();
    std::cout << prefix << "Using platform: " << platform_name << std::endl;

    /****************************
     * PART 2: DEVICE SELECTION *
     ****************************/
    std::vector<cl::Device> devices;
    platform.getDevices(CL_DEVICE_TYPE_ALL, &devices);

    if (device_str == EMPTY_STRING) {

        std::cout << prefix << "Device not chosen. Available platforms for " << platform_name << ":" << std::endl;

        if (devices.size() == 0) {
            std::cout << prefix << "No devices found on platform " << platform_name
                      << ". Check your OpenCL installation. Aborting. Good Luck." << std::endl;
            exit(1);
        }

        for (uint i = 0; i < devices.size(); i++)
            std::cout << prefix << '[' << i << "] " << devices[i].getInfo<CL_DEVICE_NAME>() << std::endl;

        device_id = -1;

        while (device_id >= devices.size()) {
            if (devices.size() > 1) {
                std::cout << prefix << "Choose a device [0-" << devices.size() - 1 << "]: ";
                std::cin >> device_id;
            }
            else device_id = 0;
            std::cin.clear();
        }

    }
    else {

        device_id = (unsigned) std::stoi(device_str);

        if (devices.size() <= device_id) {
            std::cout << prefix << "Can not use device #" << device_id << " (number of devices on selected platform: "
                      << devices.size() << "). Aborting. Good luck." << std::endl;
            exit(1);
        }

    }

    cl::Device device = devices[device_id];
    device_name = device.getInfo<CL_DEVICE_NAME>();
    std::cout << prefix << "Using device: " << device_name
              << " (device OpenCL version: " << device.getInfo<CL_DEVICE_VERSION>() << ')' << std::endl;

    /*************************************
     * PART 3: PROGRAM ENVIRONMENT SETUP *
     *************************************/
    cl::Context context({device});
    cl::Program program(context, loadProgram(kernel_file), false);
    if (program.build({device}) != CL_SUCCESS) {
        std::cout << prefix << "Error building: " << program.getBuildInfo<CL_PROGRAM_BUILD_LOG>(device) << std::endl;
        exit(1);
    }
    cl::CommandQueue queue(context, device);

    /*****************************************
     * PART X: KERNEL CREATION AND EXECUTION *
     *****************************************/

    /*** TESTING VADD FOR NOW ***/

    /*********************************************************************************************/
    int LENGTH = input_size;

    std::vector<int> h_a(LENGTH);  // a vector 
    std::vector<int> h_b(LENGTH);  // b vector  
    std::vector<int> h_c(LENGTH);  // c = a + b, from compute device

    for(int i = 0; i < LENGTH; i++) h_a[i] = h_b[i] = 2*i;

    // auto vadd = cl::make_kernel<cl::Buffer, cl::Buffer, cl::Buffer, int>(program, kernel_name);
    auto vadd = cl::Kernel(program, kernel_name.c_str());

    cl::Buffer d_a = cl::Buffer(context, begin(h_a), end(h_a), true);
    cl::Buffer d_b = cl::Buffer(context, begin(h_b), end(h_b), true);
    cl::Buffer d_c = cl::Buffer(context, CL_MEM_WRITE_ONLY, sizeof(int) * LENGTH);

    vadd.setArg(0, d_a);
    vadd.setArg(1, d_b);
    vadd.setArg(2, d_c);
    vadd.setArg(3, LENGTH);
    // vadd(
    //     cl::EnqueueArgs(
    //         queue,
    //         cl::NDRange(LENGTH)
    //     ),
    //     d_a,
    //     d_b,
    //     d_c,
    //     LENGTH);

    queue.enqueueNDRangeKernel(vadd, cl::NullRange, cl::NDRange(LENGTH), cl::NullRange);

    // queue.finish();

    // cl::copy(queue, d_c, begin(h_c), end(h_c));

    queue.enqueueReadBuffer(d_c, CL_TRUE, 0, sizeof(int) * LENGTH, h_c.data());

    for(int i = 0; i < LENGTH; i++)
        std::cout << "h_a: " << h_a[i] << " h_b: " << h_b[i] << " h_c: " << h_c[i] << std::endl;
    /*********************************************************************************************/




    return 0;
}
