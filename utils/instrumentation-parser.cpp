#include <iostream>
#include <string>

#include <llvm/IR/Module.h>
#include <llvm/IR/DebugInfoMetadata.h>
#include <llvm/IRReader/IRReader.h>
#include <llvm/Support/SourceMgr.h>

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

    /* iterate over functions, then basic blocks, then instructions */
    std::string funcname;
    unsigned funcline;
    int bbline;

    for (llvm::Module::const_iterator func = m->begin(); func != m->end(); func++) {

        if (func->isIntrinsic()) continue;
        funcname = func->getName().str();
        funcline = func->getSubprogram()->getLine();
        std::cerr << prefix << "reporting about function " << funcname << std::endl;
        /* the structure that will hold the final results - instrumentation instructions for a single function *
         * one vector for each BB, holding strings of the format "line:instruction"                            */

        std::vector<int> bblines;
        unsigned i = 1;
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
                if (loc.getLine() != 0)
                    bb_instrumentation.push_back(std::to_string(loc.getLine()) + ':' + instr->getOpcodeName());
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
