import os

from oclude.utils.interactor import Interactor
from oclude.utils.constants import *
from oclude.utils.formatter import OcludeFormatter
from oclude.utils.instrumentor import add_instrumentation_data_to_file

from pycparserext.ext_c_parser import OpenCLCParser
from pycparserext.ext_c_generator import OpenCLCGenerator
from pycparser.c_ast import Decl, PtrDecl, TypeDecl, IdentifierType, ID, FuncDef

interact = Interactor(__file__.split(os.sep)[-1])

### 1st pass tools (preprocessor) ###
preprocessor = 'cpp'

### 2nd pass tools ###
instrumentationGetter = os.path.join(bindir, 'instrumentation-parser')

### 3rd pass tools ###
cl2llCompiler = 'clang'
cl2llCompilerFlags = ['-g', '-c', '-x', 'cl', '-emit-llvm', '-S', '-cl-std=CL2.0', '-Xclang',
                      '-finclude-default-header', '-fno-discard-value-names']

def instrument_file(file, verbose):

    if not os.path.exists(file):
        interact(f'Error: {file} is not a file')
        exit(1)

    interact.set_verbosity(verbose)

    ########################################
    # step 1: remove comments / preprocess #
    ########################################
    cmdout, _ = interact.run_command('Preprocessing source file', preprocessor, file)
    with open(file, 'w') as f:
        f.writelines(filter(lambda line : line.strip() and not line.startswith('#'), cmdout.splitlines(keepends=True)))

    ############################################################################
    # step 2: add hidden counter arguments in kernels and missing curly braces #
    ############################################################################
    parser = OpenCLCParser()

    with open(file, 'r') as f:
        ast = parser.parse(f.read())

    ASTfunctions = list(filter(lambda x : isinstance(x, FuncDef), ast))
    funcCallsToEdit, kernelFuncs = [], []

    for f in ASTfunctions:
        (funcCallsToEdit, kernelFuncs)[any(x.endswith('kernel') for x in f.decl.funcspec)].append(f.decl.name)

    # there may be (helper) functions with the attribute "inline"
    # we need to avoid them, but to remember them in order to restore them later
    inlinedFuncs = []
    for func in ASTfunctions:
        if 'inline' in func.decl.funcspec:
            func.decl.funcspec = [x for x in func.decl.funcspec if x != 'inline']
            inlinedFuncs.append(func.decl.name)

    # our generator adds hidden arguments and missing curly braces
    gen = OcludeFormatter(funcCallsToEdit, kernelFuncs)

    with open(file, 'w') as f:
        f.write(gen.visit(ast))

    #########################################################################
    # step 3: instrument source code with counter incrementing where needed #
    #########################################################################

    # first take the instrumentation data from the respective tool
    # after compiling source to LLVM bitcode
    # WITHOUT allowing function inlining (to get pure data for each function)

    interact.run_command(
        'Compiling source to LLVM bitcode (1/2)', cl2llCompiler, *cl2llCompilerFlags, '-O0', '-o', templlvm, file
    )

    instrumentation_data, _ = interact.run_command(
        'Retrieving instrumentation data from LLVM bitcode', instrumentationGetter, templlvm
    )

    ### there may be a need to restore the "inline" function attribute in some functions at this point ###
    if inlinedFuncs:
        with open(file, 'r') as f:
            ast = parser.parse(f.read())
        for ext in filter(lambda x : isinstance(x, FuncDef) and x.decl.name in inlinedFuncs, ast.ext):
            ext.decl.funcspec = ['inline'] + ext.decl.funcspec
        gen = OpenCLCGenerator()
        with open(file, 'w') as f:
            f.write(gen.visit(ast))
    ### "inline" function attribute restored at this point, if it was needed to ###

    _, inliner_report = interact.run_command(
        'Compiling source to LLVM bitcode (2/2)', cl2llCompiler, *cl2llCompilerFlags, '-Rpass=inline', '-o', templlvm, file
    )
    os.remove(templlvm)

    # for each inlined function, replace the "call" with a negative "ret"
    # that means that each inlined function leads to 1 less "call" and 1 less "ret"
    inline_lines = [x.split()[0].split(':')[-3] for x in filter(lambda y : 'remark' in y, inliner_report.splitlines())]
    for inline_line in inline_lines:
        instrumentation_data = instrumentation_data.replace('|' + inline_line + ':call', '|retNOT', 1)

    # now add them to the source file, eventually instrumenting it
    add_instrumentation_data_to_file(file, kernelFuncs, instrumentation_data, parser)

    # instrumentation is done! Congrats!

    # store a prettified (i.e. easier to read/inspect) format in the cache
    with open(file, 'r') as f:
        src = f.read()
    with open(file, 'w') as f:
        for line in src.splitlines():
            if f'atom_add(& {hidden_counter_name_local}' in line or f'atom_sub(& {hidden_counter_name_local}' in line:
                instr_idx = int(line.split('[')[1].split(']')[0])
                line += f' /* {llvm_instructions[instr_idx]} */'
            f.write(line + '\n')

    if verbose:

        interact('Final instrumented source code for inspection:')
        interact('============================================================================', nl=False)
        interact('============================================================================', prompt=False)

        with open(file, 'r') as f:
            for line in f.readlines():
                interact(line, prompt=False, nl=False)

        interact('============================================================================', nl=False)
        interact('============================================================================', prompt=False)

    interact('Intrumentation completed successfully')
