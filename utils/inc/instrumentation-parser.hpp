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
