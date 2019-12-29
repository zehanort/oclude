import argparse
import subprocess as sp
from sys import argv, stderr
import os
import utils

# define the arguments of oclude
parser = argparse.ArgumentParser(
	description='oclude - the OpenCL universal driving environment'
)

parser.add_argument('infile',
	type=str,
	help='the *.cl file with the OpenCL kernel(s)'
)

parser.add_argument('-k', '--kernel',
	type=str,
	help='the name of the kernel to run from the input file',
	required=True
)

parser.add_argument('-s', '--size',
	type=int,
	help='the size of the buffer arguments of the kernel',
	required=True
)

parser.add_argument('-p', '--platform',
	type=int,
	help='the index of OpenCL platform to use (default: 0)',
	default=0
)

parser.add_argument('-d', '--device',
	type=int,
	help='the index of the OpenCL device to use (default: 0)',
	default=0
)

args = parser.parse_args()

prompt = '[' + argv[0].split('.')[0] +  ']'

instrumentor = 'instrumentor.py'
hostcodeWrapper = './hostcode-wrapper'
hostcodeWrapperFlags = [
	'-f', utils.tempfile,
	'-k', args.kernel,
	'-s', str(args.size),
	'-p', str(args.platform),
	'-d', str(args.device)
]

### STEP 1: instrument input source file ###
###  the final code ends up in tempfile  ###
instrumentationCmd = ' '.join(['python3.7', instrumentor, args.infile])
stderr.write(f'{prompt} Intrumenting source code: {instrumentationCmd}\n')

cmdout = sp.run(instrumentationCmd, stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
if (cmdout.returncode != 0):
    stderr.write(f'{prompt} Error while running {instrumentor}: {cmdout.stderr.decode("ascii")}\n')
    exit(cmdout.returncode)

### STEP 2: run the kernel ###
kernelRunCmd = ' '.join([hostcodeWrapper, *hostcodeWrapperFlags])
stderr.write(f'{prompt} Running kernel {args.kernel} from file {args.infile}: {kernelRunCmd}\n')

cmdout = sp.run(kernelRunCmd, stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
if (cmdout.returncode != 0):
    stderr.write(f'{prompt} Error while running {hostcodeWrapper}: {cmdout.stderr.decode("ascii")}\n')
    exit(cmdout.returncode)

print(cmdout.stderr.decode('ascii'))

os.remove(utils.tempfile)
