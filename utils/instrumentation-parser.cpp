#include <iostream>
#include <string>

#include <llvm/IR/Module.h>
#include <llvm/IRReader/IRReader.h>
#include <llvm/Support/SourceMgr.h>

llvm::LLVMContext context;
std::unique_ptr<llvm::Module> m;

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
        std::cerr << prefix << "problem occured while parsing IR file " << filename << std::endl;
        exit(EXIT_FAILURE);
    }

    /* iterate over functions, then basic blocks, then instructions */
    std::string funcname;
    for (llvm::Module::const_iterator func = m->begin(); func != m->end(); func++) {

        if (func->isIntrinsic()) continue;
        funcname = func->getName().str();
        std::cerr << prefix << "reporting about function " << funcname << std::endl;

        int i = 1;
        for (llvm::Function::const_iterator bb = func->begin(); bb != func->end(); bb++) {

            std::cerr << prefix << "\treporting about Basic Block #" << (i++) << std::endl;

            for (llvm::BasicBlock::const_iterator instr = bb->begin(); instr != bb->end(); instr++) {
                llvm::MDNode *metadata = instr->getMetadata("dbg");
                if (!metadata) continue;
                llvm::DebugLoc loc(metadata);
                std::cerr << prefix << "\t\tinstruction " << instr->getOpcodeName()
                          << " from source code line " << loc.getLine() << " column " << loc.getCol() << std::endl;
            }

        }

    }

    return 0;
}
