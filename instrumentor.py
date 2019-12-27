from sys import argv, stderr
import subprocess as sp
import re
import os
import utils

prompt = '[' + argv[0].split('.')[0] +  ']'
tempfile = '.oclude_tmp_instr_src.cl'
counterBuffer = f', __global int *{utils.hidden_counter_name}'

missingCurlyBracesAdder = 'clang-tidy'
missingCurlyBracesAdderFlags = ['-fix',
                                '-checks="readability-braces-around-statements"',
                                '--',
                                '-include', '/home/sotiris/projects/llvm-project/libclc/generic/include/clc/clc.h',
                                '-isystem', '/home/sotiris/projects/llvm-project/libclc/generic/include/']

braceBreaker = 'clang-format'
braceBreakerFlags = ['-style="{BreakBeforeBraces: Allman}"']

if len(argv) < 2:
    stderr.write(f'{prompt} error: no input file provided\n')
    exit(1)

if not os.path.exists(argv[1]):
    stderr.write(f'{prompt} error: {argv[1]} is not a file\n')
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
                    # print(counterBuffer, end='')
                    # print(word[j:], end=' ')
                    instrsrc += counterBuffer + word[j:] + ' '
                    break
            # print(c, end=' ' if j == len(word) - 1 else '')
            instrsrc += c + (' ' if j == len(word) - 1 else '')
        idx += 1

####################################
# step 3: add missing curly braces #
####################################
with open(tempfile, 'w') as f:
    f.write(instrsrc)

addMissingCurlyBracesCmd = ' '.join([missingCurlyBracesAdder, tempfile, *missingCurlyBracesAdderFlags])
stderr.write(f'{prompt} going to run command: {addMissingCurlyBracesCmd}\n')

cmdout = sp.run(addMissingCurlyBracesCmd, stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
if (cmdout.returncode != 0):
    stderr.write(f'{prompt} error while running {missingCurlyBracesAdder}: {cmdout.stderr.decode("ascii")}\n')
    exit(cmdout.returncode)

with open(tempfile, 'r') as f:
    instrsrc = f.read()

#################################################
# step 4: add new line before every curly brace #
#################################################
braceBreakerCmd = ' '.join([braceBreaker, *braceBreakerFlags, tempfile])
stderr.write(f'{prompt} going to run command: {braceBreakerCmd}\n')

cmdout = sp.run(braceBreakerCmd, stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
if (cmdout.returncode != 0):
    stderr.write(f'{prompt} error while running {braceBreaker}: {cmdout.stderr.decode("ascii")}\n')
    exit(cmdout.returncode)

instrsrc = cmdout.stdout.decode('ascii')

#########################################################################
# step 5: instrument source code with counter incrementing where needed #
#########################################################################


print(instrsrc)
os.remove(tempfile)
stderr.write(f'{prompt} intrumentation completed successfully\n')
