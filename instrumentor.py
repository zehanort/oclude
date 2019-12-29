from sys import argv, stderr
import subprocess as sp
import re
import os
import utils

prompt = '[' + argv[0].split('.')[0] +  ']'
tempfile = '.oclude_tmp_instr_src.cl'
templlvm = '.oclude_tmp_instr_ll.ll'

missingCurlyBracesAdder = 'clang-tidy'
missingCurlyBracesAdderFlags = ['-fix',
                                '-checks="readability-braces-around-statements"',
                                '--',
                                '-include', '/home/sotiris/projects/llvm-project/libclc/generic/include/clc/clc.h',
                                '-isystem', '/home/sotiris/projects/llvm-project/libclc/generic/include/']

braceBreaker = 'clang-format'
braceBreakerFlags = ['-style="{BreakBeforeBraces: Allman}"']

instrumentationGetter = os.path.join('utils', 'instrumentation-parser')

cl2llCompiler = 'clang'
cl2llCompilerFlags = ['-g', '-c', '-x', 'cl', '-emit-llvm',
                      '-S', '-cl-std=CL2.0', '-Xclang', '-finclude-default-header']

if len(argv) < 2:
    stderr.write(f'{prompt} Error: no input file provided\n')
    exit(1)

if not os.path.exists(argv[1]):
    stderr.write(f'{prompt} Error: {argv[1]} is not a file\n')
    exit(1)

###########################
# step 1: remove comments #
###########################
with open(argv[1], 'r') as f:
    src = utils.remove_comments(f.read())

##################################################
# step 2: add hidden counter argument in kernels #
##################################################
src = re.findall(r'\S+|\n', src)
instrsrc = ''

cnt = 0
idx = 0
kernel_mode = False
while idx < len(src):
    word = src[idx]
    ### inside a kernel function header ###
    if not kernel_mode:
        if (word == 'kernel' or word == '__kernel') and src[idx+1] == 'void':
            kernel_mode = True
            cnt = 0
        idx += 1
        instrsrc += word + ' '
    ### not inside a kernel function header ###
    else:
        for j, c in enumerate(word):
            if c == '(':
                cnt += 1
            elif c == ')':
                cnt -= 1
                # reached end of kernel declaration?
                if (cnt == 0):
                    kernel_mode = False
                    instrsrc += utils.counterBuffers + word[j:]
                    break
            instrsrc += c + (' ' if j == len(word) - 1 else '')
        idx += 1

####################################
# step 3: add missing curly braces #
####################################
with open(tempfile, 'w') as f:
    f.write(instrsrc)

addMissingCurlyBracesCmd = ' '.join([missingCurlyBracesAdder, tempfile, *missingCurlyBracesAdderFlags])
stderr.write(f'{prompt} Adding missing curly braces: {addMissingCurlyBracesCmd}\n')

cmdout = sp.run(addMissingCurlyBracesCmd, stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
if (cmdout.returncode != 0):
    stderr.write(f'{prompt} Error while running {missingCurlyBracesAdder}: {cmdout.stderr.decode("ascii")}\n')
    exit(cmdout.returncode)

#################################################
# step 4: add new line before every curly brace #
#################################################
braceBreakerCmd = ' '.join([braceBreaker, *braceBreakerFlags, tempfile])
stderr.write(f'{prompt} Breaking curly braces: {braceBreakerCmd}\n')

cmdout = sp.run(braceBreakerCmd, stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
if (cmdout.returncode != 0):
    stderr.write(f'{prompt} Error while running {braceBreaker}: {cmdout.stderr.decode("ascii")}\n')
    exit(cmdout.returncode)

with open(tempfile, 'w') as f:
    f.write(cmdout.stdout.decode('ascii'))

#########################################################################
# step 5: instrument source code with counter incrementing where needed #
#########################################################################

# first take the instrumentation data from the respective tool
# after compiling source to LLVM bitcode

cl2llCompilerCmd = ' '.join([cl2llCompiler, *cl2llCompilerFlags, '-o', templlvm, tempfile])
stderr.write(f'{prompt} Compiling source to LLVM bitcode: {cl2llCompilerCmd}\n')

cmdout = sp.run(cl2llCompilerCmd, stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
if (cmdout.returncode != 0):
    stderr.write(f'{prompt} Error while running {cl2llCompiler}: {cmdout.stderr.decode("ascii")}\n')
    exit(cmdout.returncode)

instrumentationGetterCmd = ' '.join([instrumentationGetter, templlvm])
stderr.write(f'{prompt} Instrumenting source: {instrumentationGetterCmd}\n')

cmdout = sp.run(instrumentationGetterCmd, stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
if (cmdout.returncode != 0):
    stderr.write(f'{prompt} Error while running {instrumentationGetter}: {cmdout.stderr.decode("ascii")}\n')
    exit(cmdout.returncode)

os.remove(templlvm)

instrumentation_data = cmdout.stdout.decode('ascii')

# now add them to the source file, eventually instrumenting it
utils.instrument_sourcefile(tempfile, instrumentation_data)

# instrumentation is done! Congrats!
stderr.write(f'{prompt} Final instrumented source code for inspection:\n')
with open(tempfile, 'r') as f:
    print(f.read())
os.remove(tempfile)
stderr.write(f'{prompt} Intrumentation completed successfully\n')
