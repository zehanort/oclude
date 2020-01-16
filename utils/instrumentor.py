import os
import utils
import types

from pycparserext.ext_c_parser import OpenCLCParser
from pycparserext.ext_c_generator import OpenCLCGenerator
from pycparser.c_ast import Decl, PtrDecl, TypeDecl, IdentifierType, ID, FuncDef

interact = utils.Interactor(__file__.split(os.sep)[-1])

### 0 pass tools (preprocessor) ###
preprocessor = 'cpp'

### 1st pass tools ###
missingCurlyBracesAdder = 'clang-tidy'
missingCurlyBracesAdderFlags = ['-fix',
                                '-checks="readability-braces-around-statements"',
                                '--',
                                '-include', utils.cfg.clcHeaderFile,
                                '-isystem', utils.cfg.libclcIncludePath]

### 2nd pass tools ###
braceBreaker = 'clang-format'
braceBreakerFlags = ['-style="{BreakBeforeBraces: Allman, ColumnLimit: 0}"']

### 3rd pass tools (python native) ###
hiddenCounterLocalArgument = Decl(
    name=utils.hidden_counter_name_local,
    quals=['__local'],
    storage=[],
    funcspec=[],
    type=PtrDecl(
        quals=[],
        type=TypeDecl(
            declname=utils.hidden_counter_name_local,
            quals=['__local'],
            type=IdentifierType(names=['uint'])
        )
    ),
    init=None,
    bitsize=None
)

hiddenCounterGlobalArgument = Decl(
    name=utils.hidden_counter_name_global,
    quals=['__global'],
    storage=[],
    funcspec=[],
    type=PtrDecl(
        quals=[],
        type=TypeDecl(
            declname=utils.hidden_counter_name_global,
            quals=['__global'],
            type=IdentifierType(names=['uint'])
        )
    ),
    init=None,
    bitsize=None
)

### 4th pass tools ###
instrumentationGetter = os.path.join(utils.bindir, 'instrumentation-parser')

### 5th pass tools ###
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
    with open(utils.tempfile, 'w') as f:
        f.writelines(filter(lambda line : line.strip() and not line.startswith('#'), cmdout.splitlines(keepends=True)))

    ####################################
    # step 2: add missing curly braces #
    ####################################
    interact.run_command('Adding missing curly braces', missingCurlyBracesAdder, utils.tempfile, *missingCurlyBracesAdderFlags)

    ##################################################
    # step 3: add hidden counter argument in kernels #
    ##################################################
    parser = OpenCLCParser()

    with open(utils.tempfile, 'r') as f:
        ast = parser.parse(f.read())

    ASTfunctions = list(filter(lambda x : isinstance(x, FuncDef), ast))
    funcCallsToEdit, kernelFuncs = [], []

    for f in ASTfunctions:
        (funcCallsToEdit, kernelFuncs)[any(x.endswith('kernel') for x in f.decl.funcspec)].append(f.decl.name)

    for func in ASTfunctions:
        func.decl.type.args.params.append(hiddenCounterLocalArgument)
        if func.decl.name in kernelFuncs:
            func.decl.type.args.params.append(hiddenCounterGlobalArgument)

    # there may be (helper) functions with the attribute "inline"
    # we need to avoid them, but to remember them in order to restore them later
    inlinedLines = []
    for func in ASTfunctions:
        if 'inline' in func.decl.funcspec:
            inlinedLines.append(func.coord.line)
            func.decl.funcspec = [x for x in func.decl.funcspec if x != 'inline']

    gen = OpenCLCGenerator()
    old_visit_FuncCall = gen.visit_FuncCall

    def new_visit_FuncCall(self, n):
        if n.name.name in funcCallsToEdit:
            x = n.args.exprs.append(ID(utils.hidden_counter_name_local))
        return old_visit_FuncCall(n)

    gen.visit_FuncCall = types.MethodType(new_visit_FuncCall, gen)

    with open(utils.tempfile, 'w') as f:
        f.write(gen.visit(ast))

    #################################################
    # step 4: add new line before every curly brace #
    #################################################
    cmdout, _ = interact.run_command('Breaking curly braces', braceBreaker, *braceBreakerFlags, utils.tempfile)
    with open(utils.tempfile, 'w') as f:
        f.writelines(filter(lambda line : line.strip(), cmdout.splitlines(keepends=True)))

    #########################################################################
    # step 5: instrument source code with counter incrementing where needed #
    #########################################################################

    # first take the instrumentation data from the respective tool
    # after compiling source to LLVM bitcode
    # WITHOUT allowing function inlining (to get pure data for each function)

    interact.run_command(
        'Compiling source to LLVM bitcode (1/2)', cl2llCompiler, *cl2llCompilerFlags, '-fno-inline', '-o', utils.templlvm, utils.tempfile
    )

    instrumentation_data, _ = interact.run_command(
        'Retrieving instrumentation data from LLVM bitcode', instrumentationGetter, utils.templlvm
    )

    # there may be a need to restore the "inline" function attribute in some functions at this point
    if inlinedLines:

        with open(utils.tempfile, 'r') as f:
            src = f.read().splitlines(keepends=True)

        # restore "inline" function attribute wherever it was emitted
        for line in inlinedLines:
            src[line - 1] = 'inline ' + src[line - 1]

        with open(utils.tempfile, 'w') as f:
            f.writelines(src)
    # "inline" function attribute restored at this point, if it was needed to

    _, inliner_report = interact.run_command(
        'Compiling source to LLVM bitcode (2/2)', cl2llCompiler, *cl2llCompilerFlags, '-Rpass=inline', '-o', utils.templlvm, utils.tempfile
    )
    os.remove(utils.templlvm)

    # for each inlined function, replace the "call" with a negative "ret"
    # that means that each inlined function leads to 1 less "call" and 1 less "ret"
    inline_lines = [x.split()[0].split(':')[-3] for x in filter(lambda y : 'remark' in y, inliner_report.splitlines())]
    for inline_line in inline_lines:
        instrumentation_data = instrumentation_data.replace(inline_line + ':call', inline_line + ':retNOT', 1)

    # now add them to the source file, eventually instrumenting it
    utils.add_instrumentation_data_to_file(utils.tempfile, kernelFuncs, instrumentation_data)

    # instrumentation is done! Congrats!

    if verbose:

        cmdout, _ = interact.run_command('Prettifing instrumented source code', braceBreaker, *braceBreakerFlags, utils.tempfile)
        with open(utils.tempfile, 'w') as f:
            f.write(cmdout)

        interact('Final instrumented source code for inspection:')
        interact('============================================================================', nl=False)
        interact('============================================================================', prompt=False)

        with open(utils.tempfile, 'r') as f:
            for line in f.readlines():
                interact(line, prompt=False, nl=False)

        interact('============================================================================', nl=False)
        interact('============================================================================', prompt=False)

    interact('Intrumentation completed successfully')
