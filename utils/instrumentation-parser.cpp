#include <iostream>
#include <string>
#include <vector>
#include <unordered_map>
#include <algorithm>

#include <llvm/IR/Module.h>
#include <llvm/IR/Instructions.h>
#include <llvm/IR/Operator.h>
#include <llvm/IR/DebugInfoMetadata.h>
#include <llvm/IRReader/IRReader.h>
#include <llvm/Support/SourceMgr.h>
#include <llvm/Support/Casting.h>

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

int main(int argc, char const *argv[]) {

    std::string filename = std::string(__FILE__);
    std::string appname = filename.substr(0, filename.find_last_of("."));
    std::string prefix = "[" + appname + "] ";

    if (argc < 2) {
        std::cerr << prefix << "no input file given" << std::endl;
        exit(EXIT_FAILURE);
    }

    /* parse input file */
    filename = argv[1];
    llvm::SMDiagnostic error;
    m = parseIRFile(filename, error, context);

    if(!m) {
        std::cerr << prefix << "problem occured while parsing IR file " << filename << ": " << error.getMessage().str() << std::endl;
        exit(EXIT_FAILURE);
    }

    /* the structure that will hold the instrumentation for all the functions of the module */
    instrumentation_t instrumentation;

    /* find the kernel functions */
    std::vector<std::string> kernels;
    for (auto it = m->getFunctionList().begin(); it != m->getFunctionList().end(); it++)
        if (it->getCallingConv() == llvm::CallingConv::SPIR_KERNEL)
            kernels.push_back(it->getName().str());

    /* iterate over functions, then basic blocks, then instructions */
    std::string funcname;
    unsigned funcline;
    int bbline;
    bool is_kernel;
    std::unordered_map<std::string, unsigned> arg_addr_spaces;

    for (llvm::Module::const_iterator func = m->begin(); func != m->end(); func++) {

        if (func->isIntrinsic()) continue;
        funcname  = func->getName().str();
        funcline  = func->getSubprogram()->getLine();
        is_kernel = std::find(kernels.begin(), kernels.end(), funcname) != kernels.end();
        std::cerr << prefix << "reporting about function " << funcname << (is_kernel ? " (kernel function)" : "") << std::endl;

        /*
         If the current function is a kernel, we need to differentiate between the address spaces
         of the operands of the load/store instructions.
         If the current fucntion is not a kernel, we will label these mem ops as "{load,store}_helpfunc"
         */
        if (is_kernel) {
            /* create a dictionary from kernel argument names to address spaces */
            arg_addr_spaces.clear();
            auto *argmeta = func->getMetadata("kernel_arg_addr_space");
            auto current_arg = func->arg_begin();
            for (auto x = argmeta->op_begin(); x != argmeta->op_end(); x++) {
                auto addrspace = llvm::dyn_cast<llvm::ConstantInt>(llvm::cast<llvm::ValueAsMetadata>(x->get())->getValue());
                if (addrspace->equalsInt(ADDRESS_SPACE::PRIVATE))
                    arg_addr_spaces[current_arg->getName().str()] = ADDRESS_SPACE::PRIVATE;
                else if (addrspace->equalsInt(ADDRESS_SPACE::GLOBAL))
                    arg_addr_spaces[current_arg->getName().str()] = ADDRESS_SPACE::GLOBAL;
                else if (addrspace->equalsInt(ADDRESS_SPACE::CONSTANT))
                    arg_addr_spaces[current_arg->getName().str()] = ADDRESS_SPACE::CONSTANT;
                else if (addrspace->equalsInt(ADDRESS_SPACE::LOCAL))
                    arg_addr_spaces[current_arg->getName().str()] = ADDRESS_SPACE::LOCAL;
                current_arg++;
            }
        }

        std::vector<int> bblines;
        unsigned i = 1;
        std::string operand, addrspace_notation;
        for (llvm::Function::const_iterator bb = func->begin(); bb != func->end(); bb++) {

            std::cerr << prefix << "\treporting about Basic Block #" << (i++) << std::endl;
            /* reset bbline */
            bbline = -1;
            bb_instrumentation_t bb_instrumentation;

            for (llvm::BasicBlock::const_iterator instr = bb->begin(); instr != bb->end(); instr++) {
                llvm::MDNode *metadata = instr->getMetadata("dbg");
                if (!metadata) continue;
                llvm::DebugLoc loc(metadata);
                std::cerr << prefix << "\t\tinstruction " << instr->getOpcodeName()
                          << " from source code line " << loc.getLine() << " column " << loc.getCol() << std::endl;

                /* check if bbline is updated */
                if ((loc.getLine() != 0) && (bbline == -1))
                    bbline = loc.getLine() - 1;
                /* if the condition below holds, we need to update our instrumentation data */
                if (loc.getLine() != 0) {
                    std::string line = std::to_string(loc.getLine());
                    /* special handling for load/store operations */
                    if (llvm::isa<llvm::LoadInst>(instr)) {

                        if (auto *gep = llvm::dyn_cast<llvm::GEPOperator>(instr->getOperand(0)))
                            operand = gep->getPointerOperand()->getName().str();
                        else
                            operand = instr->getOperand(0)->getName().str();

                        if (is_kernel) {
                            std::cerr << "AAAAAAAAAAAAAAAAA " << operand << ' ' << arg_addr_spaces[operand] <<std::endl;
                            switch (arg_addr_spaces[operand]) {
                                case ADDRESS_SPACE::PRIVATE:
                                    addrspace_notation = "private";
                                    break;
                                case ADDRESS_SPACE::GLOBAL:
                                    addrspace_notation = "global";
                                    break;
                                case ADDRESS_SPACE::CONSTANT:
                                    addrspace_notation = "constant";
                                    break;
                                case ADDRESS_SPACE::LOCAL:
                                    addrspace_notation = "local";
                                    break;
                            }
                            bb_instrumentation.push_back(line + ":load " + addrspace_notation);
                        }
                        else
                            bb_instrumentation.push_back(line + ":load callee");
                    }
                    else if (llvm::isa<llvm::StoreInst>(instr)) {

                        if (auto *gep = llvm::dyn_cast<llvm::GEPOperator>(instr->getOperand(1)))
                            operand = gep->getPointerOperand()->getName().str();
                        else
                            operand = instr->getOperand(1)->getName().str();

                        if (is_kernel) {
                            std::cerr << "BBBBBBBBBBBBBBBB " << operand << ' ' << arg_addr_spaces[operand] <<std::endl;
                            switch (arg_addr_spaces[operand]) {
                                case ADDRESS_SPACE::PRIVATE:
                                    addrspace_notation = "private";
                                    break;
                                case ADDRESS_SPACE::GLOBAL:
                                    addrspace_notation = "global";
                                    break;
                                case ADDRESS_SPACE::CONSTANT:
                                    addrspace_notation = "constant";
                                    break;
                                case ADDRESS_SPACE::LOCAL:
                                    addrspace_notation = "local";
                                    break;
                            }
                            bb_instrumentation.push_back(line + ":store " + addrspace_notation);
                        }
                        else
                            bb_instrumentation.push_back(line + ":store callee");
                    }
                    else
                        bb_instrumentation.push_back(std::to_string(loc.getLine()) + ':' + instr->getOpcodeName());
                }
            }

            std::cerr << prefix << "\tDONE reporting about Basic Block #" << (i-1) << " which started at line " << bbline << std::endl;
            instrumentation[funcname + ':' + std::to_string(bbline)] = bb_instrumentation;

        }

    }

    /* instrumentation info gathered; dump it in a python - friendly way for parsing */
    std::string funcname_bbline;
    for (auto bb_instrumentation : instrumentation) {
        funcname_bbline = bb_instrumentation.first;
        std::cout << funcname_bbline << '|';
        for (std::string instrumentation_instruction : bb_instrumentation.second)
            std::cout << instrumentation_instruction << '|';
        std::cout << std::endl;
    }

    return 0;
}
