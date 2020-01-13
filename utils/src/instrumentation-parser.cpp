#include "instrumentation-parser.hpp"

int main(int argc, char const *argv[]) {

    if (argc < 2) {
        print_message.usage();
        exit(EXIT_FAILURE);
    }

    parse_input_file(argv[1]);

    /* the structure that will hold the instrumentation for all the functions of the module */
    instrumentation_t instrumentation;

    /* the following function iterates over module functions, then basic blocks, then instructions */
    instrumentation = get_instrumentation_info_from_module();

    /* instrumentation info gathered; dump it in a python - friendly way for parsing */
    dump_instrumentation_info(instrumentation);

    return 0;
}
