#include <iostream>
#include <fstream>
#include <variant>
#include <cstdlib>
#include <ctime>
#include <random>
#ifdef __APPLE__
    #include <OpenCL/cl.hpp>
#else
    #include <CL/cl.hpp>
#endif

#include "typegen.hpp"

#define OCLUDE_COUNTER_LOCAL  (std::string("ocludeHiddenCounterLocal"))
#define OCLUDE_COUNTER_GLOBAL (std::string("ocludeHiddenCounterGlobal"))
#define EMPTY_STRING          (std::string(""))
#define COUNTER_BUFFER_SIZE   74

class MessagePrinter {
private:
    std::string appname, prompt;
public:
    MessagePrinter() {
        appname = std::string(__FILE__);
        appname = appname.substr(appname.find_last_of("/") + 1, appname.size() - 1);
        appname = appname.substr(0, appname.find_last_of("."));
        prompt = "[" + appname + "] ";
    }
    void operator()(std::string message, bool nl=true) {
        std::cerr << prompt << message;
        if (nl) std::cerr << std::endl;
    }
    void usage() {
        std::cerr << "usage: ./" << appname << ' ' << "<file> <kernel> <size> <work groups> [<platform>] [<device>]" << std::endl;
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

/* for pretty-printing only */
std::string resolve_address_qualifier(int address_qual) {
    switch (address_qual) {
        case CL_KERNEL_ARG_ADDRESS_GLOBAL:   return "global";
        case CL_KERNEL_ARG_ADDRESS_CONSTANT: return "constant";
        case CL_KERNEL_ARG_ADDRESS_LOCAL:    return "local";
        default:                             return "private";
    }
}
