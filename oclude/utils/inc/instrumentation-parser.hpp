#ifndef __IP_HPP__
#define __IP_HPP__

#include <iostream>
#include <string>
#include <vector>

#include <llvm/IR/Module.h>
#include <llvm/IR/Instructions.h>
#include <llvm/IR/Operator.h>
#include <llvm/IR/DebugInfoMetadata.h>
#include <llvm/IRReader/IRReader.h>
#include <llvm/Support/SourceMgr.h>
#include <llvm/Support/Casting.h>

#include "message-printer.hpp"

MessagePrinter print_message(__FILE__, "<.ll or .bc file>");

/*
 * OpenCL address spaces, as per the documentation here:
 * https://www.khronos.org/registry/SPIR/specs/spir_spec-1.2.pdf
 * (section 2.2: Address space qualifiers)
 */
enum ADDRESS_SPACE { PRIVATE = 0, GLOBAL, CONSTANT, LOCAL };

llvm::LLVMContext context;
std::unique_ptr<llvm::Module> m;

typedef std::vector<std::string>                    bb_instrumentation_t;
typedef std::map<std::string, bb_instrumentation_t> instrumentation_t;

inline void parse_input_file(std::string filename) {
    llvm::SMDiagnostic error;
    m = parseIRFile(filename, error, context);
    if(!m) {
        print_message("problem occured while parsing IR file " + filename + ": " + error.getMessage().str());
        exit(EXIT_FAILURE);
    }
    return;
}

inline std::vector<std::string> find_kernel_functions_in_module() {
    std::vector<std::string> kernels;
    for (auto it = m->getFunctionList().begin(); it != m->getFunctionList().end(); it++)
        if (it->getCallingConv() == llvm::CallingConv::SPIR_KERNEL)
            kernels.push_back(it->getName().str());
    return kernels;
}

inline std::string get_address_space_of_operand(uint addrspace) {
    switch (addrspace) {
        case ADDRESS_SPACE::GLOBAL:   return "global";
        case ADDRESS_SPACE::CONSTANT: return "constant";
        case ADDRESS_SPACE::LOCAL:    return "local";
        default:                      return "private";
    }
}

inline std::string resolve_memop(auto instr, bool is_kernel) {
    if (is_kernel) return get_address_space_of_operand(instr->getPointerAddressSpace());
    return "callee";
}

inline instrumentation_t get_instrumentation_info_from_module() {

    /* the map that will hold all the instrumentation info that will be gathered */
    instrumentation_t instrumentation;

    std::vector<std::string> kernels = find_kernel_functions_in_module();
    std::string funcname;
    bool is_kernel;

    for (llvm::Module::const_iterator func = m->begin(); func != m->end(); func++) {

        if (func->isIntrinsic()) continue;
        funcname  = func->getName().str();
        is_kernel = std::find(kernels.begin(), kernels.end(), funcname) != kernels.end();
        print_message("reporting about function " + funcname + (is_kernel ? " (kernel function)" : ""));

        unsigned i = 1;
        for (llvm::Function::const_iterator bb = func->begin(); bb != func->end(); bb++) {

            print_message("\treporting about Basic Block #" + std::to_string(i));
            bb_instrumentation_t bb_instrumentation;

            for (const auto &instr : bb->instructionsWithoutDebug()) {
                llvm::MDNode *metadata = instr.getMetadata("dbg");
                llvm::DebugLoc loc(metadata);
                std::string extra_info = loc ? " from source code line " + std::to_string(loc.getLine()) +
                                               " column " + std::to_string(loc.getCol())
                                             : "";
                print_message("\t\tinstruction " + (std::string)instr.getOpcodeName() + extra_info);
                if (!loc || loc.getLine() != 0) {
                    /* special handling for load/store operations */
                    if (llvm::isa<llvm::LoadInst>(&instr))
                        bb_instrumentation.push_back("load " + resolve_memop(llvm::cast<llvm::LoadInst>(&instr), is_kernel));
                    else if (llvm::isa<llvm::StoreInst>(&instr))
                        bb_instrumentation.push_back("store " + resolve_memop(llvm::cast<llvm::StoreInst>(&instr), is_kernel));
                    else if (llvm::isa<llvm::CallInst>(&instr)) {
                        /* we discard unlocalized calls as internal to LLVM */
                        if (loc)
                            bb_instrumentation.push_back(std::to_string(loc.getLine()) + ':' + "call");
                    }
                    else
                        bb_instrumentation.push_back(instr.getOpcodeName());
                }
            }

            print_message("\tDONE reporting about Basic Block #" + std::to_string(i));
            instrumentation[funcname + ':' + std::to_string(i++)] = bb_instrumentation;

        }

    }

    return instrumentation;
}

inline void dump_instrumentation_info(instrumentation_t instrumentation) {
    std::string funcname_bbline;
    for (auto bb_instrumentation : instrumentation) {
        funcname_bbline = bb_instrumentation.first;
        std::cout << funcname_bbline << '|';
        for (std::string instrumentation_instruction : bb_instrumentation.second)
            std::cout << instrumentation_instruction << '|';
        std::cout << std::endl;
    }
    return;
}

#endif
