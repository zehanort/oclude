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

parser.add_argument('-w', '--work-groups',
	type=int,
	help='the total number of work groups',
	required=True,
	dest='work_groups'
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

print_message = utils.MessagePrinter(argv[0])

instrumentor = 'instrumentor.py'
hostcodeWrapper = './hostcode-wrapper'
hostcodeWrapperFlags = [
	utils.tempfile,
	args.kernel,
	str(args.size),
	str(args.work_groups),
	str(args.platform),
	str(args.device)
]

### STEP 1: instrument input source file ###
###  the final code ends up in tempfile  ###
instrumentationCmd = ' '.join(['python3.7', instrumentor, args.infile])
print_message(f'Intrumenting source code: {instrumentationCmd}')

cmdout = sp.run(instrumentationCmd, stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
if (cmdout.returncode != 0):
    print_message(f'Error while running {instrumentor}: {cmdout.stderr.decode("ascii")}')
    exit(cmdout.returncode)

print_message(cmdout.stderr.decode('ascii'), prompt=False)

### STEP 2: run the kernel ###
kernelRunCmd = ' '.join([hostcodeWrapper, *hostcodeWrapperFlags])
print_message(f'Running kernel {args.kernel} from file {args.infile}: {kernelRunCmd}')

cmdout = sp.run(kernelRunCmd, stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
if (cmdout.returncode != 0):
    print_message(f'Error while running {hostcodeWrapper}: {cmdout.stderr.decode("ascii")}')
    exit(cmdout.returncode)

print_message(cmdout.stderr.decode('ascii'), prompt=False)

### STEP 3: parse hostcode-wrapper output and dump a oclgrind-like output ###
instcounts = sorted(
	[
		(utils.llvm_instructions[instIdx], instCnt)
		for instIdx, instCnt in map(
			lambda x : map(int, x),
			map(
				lambda x : x.split(':'),
				cmdout.stdout.decode('ascii').splitlines()
			)
		)
		if instCnt != 0
	],
	key=lambda x : x[1],
	reverse=True
)

print_message('Kernel run completed successfully')

print(f"Instructions executed for kernel '{args.kernel}':")
for instName, instCnt in instcounts:
	print(f'{instCnt : 16} - {instName}')

# os.remove(utils.tempfile)
