import subprocess as sp
import os
import utils
import types

from pycparserext.ext_c_parser import OpenCLCParser
from pycparserext.ext_c_generator import OpenCLCGenerator
from pycparser.c_ast import Decl, PtrDecl, TypeDecl, IdentifierType, ID, FuncDef

print_message = utils.MessagePrinter(__file__.split(os.sep)[-1])

### 0 pass tools (preproccessor) ###
preproccessor = 'cpp'

### 1st pass tools ###
missingCurlyBracesAdder = 'clang-tidy'
missingCurlyBracesAdderFlags = ['-fix',
                                '-checks="readability-braces-around-statements"',
                                '--',
                                '-include', '/home/sotiris/projects/llvm-project/libclc/generic/include/clc/clc.h',
                                '-isystem', '/home/sotiris/projects/llvm-project/libclc/generic/include/']

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
instrumentationGetter = os.path.join('utils', 'instrumentation-parser')

### 5th pass tools ###
cl2llCompiler = 'clang'
cl2llCompilerFlags = ['-g', '-c', '-x', 'cl', '-emit-llvm',
                      '-S', '-cl-std=CL2.0', '-Xclang', '-finclude-default-header']

def instrument_file(file, verbose=False):

    if not os.path.exists(file):
        print_message(f'Error: {file} is not a file')
        exit(1)

    ########################################
    # step 1: remove comments / preprocess #
    ########################################
    preproccessingCmd = ' '.join([preproccessor, file])
    print_message('Preproccessing source file' + (f': {preproccessingCmd}' if verbose else ''))
    cmdout = sp.run(preproccessingCmd, stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
    if (cmdout.returncode != 0):
        print_message(f'Error while running {preproccessor}: {cmdout.stderr.decode("ascii")}')
        exit(cmdout.returncode)

    with open(utils.tempfile, 'w') as f:
        f.writelines(filter(lambda line : line and not line.startswith('#'), cmdout.stdout.decode('ascii').splitlines()))

    ####################################
    # step 2: add missing curly braces #
    ####################################
    addMissingCurlyBracesCmd = ' '.join([missingCurlyBracesAdder, utils.tempfile, *missingCurlyBracesAdderFlags])
    print_message('Adding missing curly braces' + (f': {addMissingCurlyBracesCmd}' if verbose else ''))

    cmdout = sp.run(addMissingCurlyBracesCmd, stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
    if (cmdout.returncode != 0):
        print_message(f'Error while running {missingCurlyBracesAdder}: {cmdout.stderr.decode("ascii")}')
        exit(cmdout.returncode)

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
    braceBreakerCmd = ' '.join([braceBreaker, *braceBreakerFlags, utils.tempfile])
    print_message('Breaking curly braces' + (f': {braceBreakerCmd}' if verbose else ''))

    cmdout = sp.run(braceBreakerCmd, stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
    if (cmdout.returncode != 0):
        print_message(f'Error while running {braceBreaker}: {cmdout.stderr.decode("ascii")}')
        exit(cmdout.returncode)

    with open(utils.tempfile, 'w') as f:
        f.write(cmdout.stdout.decode('ascii'))

    #########################################################################
    # step 5: instrument source code with counter incrementing where needed #
    #########################################################################

    # first take the instrumentation data from the respective tool
    # after compiling source to LLVM bitcode

    cl2llCompilerCmd = ' '.join([cl2llCompiler, *cl2llCompilerFlags, '-o', utils.templlvm, utils.tempfile])
    print_message('Compiling source to LLVM bitcode' + (f': {cl2llCompilerCmd}' if verbose else ''))

    cmdout = sp.run(cl2llCompilerCmd, stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
    if (cmdout.returncode != 0):
        print_message(f'Error while running {cl2llCompiler}: {cmdout.stderr.decode("ascii")}')
        exit(cmdout.returncode)

    instrumentationGetterCmd = ' '.join([instrumentationGetter, utils.templlvm])
    print_message('Instrumenting source' + (f': {instrumentationGetterCmd}' if verbose else ''))

    cmdout = sp.run(instrumentationGetterCmd, stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
    if (cmdout.returncode != 0):
        print_message(f'Error while running {instrumentationGetter}: {cmdout.stderr.decode("ascii")}')
        exit(cmdout.returncode)

    os.remove(utils.templlvm)

    instrumentation_data = cmdout.stdout.decode('ascii')

    # now add them to the source file, eventually instrumenting it
    utils.add_instrumentation_data_to_file(utils.tempfile, instrumentation_data)

    # instrumentation is done! Congrats!
    print_message('Prettifing instrumented source code' + (f': {braceBreakerCmd}' if verbose else ''))

    cmdout = sp.run(braceBreakerCmd, stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
    if (cmdout.returncode != 0):
        print_message(f'Error while running {braceBreaker}: {cmdout.stderr.decode("ascii")}')
        exit(cmdout.returncode)

    with open(utils.tempfile, 'w') as f:
        f.write(cmdout.stdout.decode('ascii'))

    if verbose:
        print_message('Final instrumented source code for inspection:')
        with open(utils.tempfile, 'r') as f:
            for line in f.readlines():
                print_message(line, prompt=False)

    print_message('Intrumentation completed successfully')
