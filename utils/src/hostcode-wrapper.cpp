#include "hostcode-wrapper.hpp"

int main(int argc, char const *argv[]) {

    if (argc < 5) {
        print_message.usage();
        exit(1);
    }

    std::string kernel_file = argv[1];
    std::string kernel_name = argv[2];
    uint LENGTH = std::stoi(argv[3]);
    uint WORK_GROUPS = std::stoi(argv[4]);
    std::string platform_str;
    if (argc > 5) platform_str = argv[5];
    else          platform_str = EMPTY_STRING;
    std::string device_str;
    if (argc > 6) device_str = argv[6];
    else          device_str = EMPTY_STRING;
    uint platform_id, device_id;
    std::string platform_name, device_name;
    set_limits(LENGTH);

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
            print_message('[' + std::to_string(i) + "] " + platforms[i].getInfo<CL_PLATFORM_NAME>());

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

        platform_id = (uint)std::stoi(platform_str);

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

        device_id = (uint)std::stoi(device_str);

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
    print_message("Kernel name: " + kernel_name);
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
    for (cl_uint i = 0; i < nargs; i++) {
        if ((kernel.getArgInfo<CL_KERNEL_ARG_NAME>(i).rfind(OCLUDE_COUNTER_LOCAL, 0) == 0) ||
            (kernel.getArgInfo<CL_KERNEL_ARG_NAME>(i).rfind(OCLUDE_COUNTER_GLOBAL, 0) == 0))
            continue;
        print_message("Kernel arg " + std::to_string(i)
                                    + ": " + kernel.getArgInfo<CL_KERNEL_ARG_NAME>(i)
                                    + " (" + kernel.getArgInfo<CL_KERNEL_ARG_TYPE_NAME>(i)
                                    + ", " + resolve_address_qualifier(kernel.getArgInfo<CL_KERNEL_ARG_ADDRESS_QUALIFIER>(i)) + ')'
        );
    }

    /*** Step 2: create an object for each kernel argument ***/
    kernel_args_t kernel_args;
    cl::Buffer counterBuffer;

    // an array of buffers for the kernel arguments
    cl::Buffer argumentBuffers[nargs];
    std::vector<void *> arguments;

    // initialization of several random generators needed to populate args
    std::random_device rd;
    std::mt19937 gen(rd());
    std::uniform_int_distribution<cl_int> int_dis(-LENGTH, LENGTH);
    std::uniform_int_distribution<cl_uint> uint_dis(0, LENGTH);
    std::uniform_real_distribution<cl_float> float_dis(-LENGTH, LENGTH);

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
            kernel_args.push_back(v_uint(COUNTER_BUFFER_SIZE * WORK_GROUPS));
            for (uint j = 0; j < COUNTER_BUFFER_SIZE * WORK_GROUPS; j++)
                std::get<v_uint>(kernel_args.back())[j] = 0;
            argumentBuffers[i] = cl::Buffer(context, begin(std::get<v_uint>(kernel_args.back())), end(std::get<v_uint>(kernel_args.back())), false);
            kernel.setArg(i, argumentBuffers[i]);
        }

        // handle the real kernel arguments
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

    /*** Step 3: run kernel ***/
    print_message("Enqueuing kernel with Global NDRange = " + std::to_string(LENGTH) + " and Local NDRange = " + std::to_string(LENGTH / WORK_GROUPS));
    queue.enqueueNDRangeKernel(kernel, cl::NullRange, cl::NDRange(LENGTH), cl::NDRange(LENGTH / WORK_GROUPS));

    /*** Step 4: read counter buffer ***/
    v_uint globalCounter(COUNTER_BUFFER_SIZE * WORK_GROUPS);
    queue.enqueueReadBuffer(argumentBuffers[nargs-1], CL_TRUE, 0, sizeof(cl_uint) * COUNTER_BUFFER_SIZE * WORK_GROUPS, globalCounter.data());

    /*** Step 5: aggregate instruction counts across work groups ***/
    v_uint finalCounter(COUNTER_BUFFER_SIZE, 0);
    for (uint i = 0; i < COUNTER_BUFFER_SIZE; i++)
        for (uint j = 0; j < WORK_GROUPS; j++)
            finalCounter[i] += globalCounter[i + j * COUNTER_BUFFER_SIZE];

    /*** Step 6: report instruction counts ***/
    for (uint i = 0; i < finalCounter.size(); i++)
        std::cout << i << ": " << finalCounter[i] << std::endl;

    for (auto x : arguments) free(x);

    return 0;
}
