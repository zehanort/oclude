#include "hostcode-wrapper.hpp"

int main(int argc, char const *argv[]) {

    if (argc < 5) {
        print_message.usage();
        exit(1);
    }

    OpenCLutils oclutils;

    // initialize the basic parameters for the execution of the hostcode wrapper
    auto [
        kernel_file,
        kernel_name,
        LENGTH,
        WORK_GROUPS,
        platform_id,
        device_id
    ] = oclutils.parse_arguments(argc, argv);

    // initialize the limits of primitive types based on user input
    typegen::set_limits(LENGTH);

    /******************************
     * PART 1: PLATFORM SELECTION *
     ******************************/
    auto platform = oclutils.cl_get_platform(platform_id);

    /****************************
     * PART 2: DEVICE SELECTION *
     ****************************/
    auto device = oclutils.cl_get_device(platform, device_id);

    /************************************
     * PART 3: KERNEL ENVIRONMENT SETUP *
     ************************************/
    auto [ kernel, queue ] = oclutils.cl_setup_kernel(device, kernel_file, kernel_name);

    /*****************************************
     * PART 4: KERNEL CREATION AND EXECUTION *
     *****************************************/

    /*** Step 1: identify kernel arguments ***/
    oclutils.report_kernel_arguments(kernel);

    /*** Step 2: create an object for each kernel argument ***/
    oclutils.initialize_kernel_arguments(kernel, LENGTH, WORK_GROUPS);

    /*** Step 3: run kernel ***/
    print_message("Enqueuing kernel with Global NDRange = " + std::to_string(LENGTH) + " and Local NDRange = " + std::to_string(LENGTH / WORK_GROUPS));
    queue.enqueueNDRangeKernel(kernel, cl::NullRange, cl::NDRange(LENGTH), cl::NDRange(LENGTH / WORK_GROUPS));

    /*** Step 4: read counter buffer ***/
    std::vector<uint> globalCounter(COUNTER_BUFFER_SIZE * WORK_GROUPS);
    queue.enqueueReadBuffer(oclutils.get_global_counter(), CL_TRUE, 0, sizeof(cl_uint) * COUNTER_BUFFER_SIZE * WORK_GROUPS, globalCounter.data());

    /*** Step 5: aggregate instruction counts across work groups and report them ***/
    oclutils.report_instruction_counts(globalCounter, WORK_GROUPS);

    return 0;
}
