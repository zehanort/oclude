import argparse
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
	help='the index of the OpenCL platform to use (default: 0)',
	default=0
)

parser.add_argument('-d', '--device',
	type=int,
	help='the index of the OpenCL device to use (default: 0)',
	default=0
)

parser.add_argument('-v', '--verbose',
	help='toggle verbose output (default: false)',
	action='store_true'
)

parser.add_argument('-i', '--inst-counts',
	help='count the LLVM instructions that were executed and dump them to stdout',
	dest='instcounts',
	action='store_true'
)

parser.add_argument('-t', '--time-it',
	help='measure kernel execution time and dump it to stdout',
	dest='timeit',
	action='store_true'
)

args = parser.parse_args()

interact = utils.Interactor(__file__.split(os.sep)[-1])
interact.set_verbosity(args.verbose)

# some sanity checks
if not os.path.exists(utils.cfg.clcHeaderFile) or not os.path.exists(utils.cfg.libclcIncludePath):
	interact('ERROR: paths to libclc header file and/or include directory are invalid.')
	interact('Have you set them correctly before running oclude?')
	interact('If not, they are located in the file ' + os.path.abspath(os.path.join('utils', 'cfg', '__init__.py')))
	exit(1)

if args.instcounts and args.timeit:
	interact('WARNING: Instruction count and execution time measurement were both requested.')
	interact('This will result in the time measurement of the instrumented kernel and not the original.')
	interact('Proceed? [y/N] ', nl=False)
	if input() != 'y':
		exit(0)

if args.size < args.work_groups or args.size % args.work_groups != 0:
	interact('size must be a multiple of work_groups')
	exit(1)

if args.size // args.work_groups <= 8:
	interact('WARNING: Size not being greater than 8 * work_groups will most likely lead to invalid results.')
	interact('Proceed? [y/N] ', nl=False)
	if input() != 'y':
		exit(0)

hostcodeWrapper = os.path.join(utils.bindir, 'hostcode-wrapper')
hostcodeWrapperFlags = [
	utils.tempfile,
	args.kernel,
	str(args.size),
	str(args.work_groups),
	'y' if args.instcounts else 'n',
	'y' if args.timeit else 'n',
	str(args.platform),
	str(args.device)
]

### STEP 1: instrument input source file ###
###  the final code ends up in tempfile  ###
interact('Instrumenting source code')
utils.instrument_file(os.path.abspath(args.infile), args.verbose)

### STEP 2: run the kernel ###
cmdout, cmderr = interact.run_command(f'Running kernel {args.kernel} from file {args.infile}', hostcodeWrapper, *hostcodeWrapperFlags)
interact(cmderr, prompt=False, nl=False)
os.remove(utils.tempfile)
interact('Kernel run completed successfully')

### STEP 3: parse hostcode-wrapper output ###
cmdout = cmdout.splitlines()

if args.timeit:
	nsecs = float(cmdout[-1].split(':')[1])
	cmdout = cmdout[:-1]

if args.instcounts:
	instcounts = sorted(
		[
			(utils.llvm_instructions[instIdx], instCnt)
			for instIdx, instCnt in map(
				lambda x : map(int, x),
				map(lambda x : x.split(':'), cmdout)
			)
			if instCnt != 0
		],
		key=lambda x : x[1],
		reverse=True
	)

### STEP 4: dump an oclgrind-like output (if requested by user) ###
if args.instcounts:
	print(f"Instructions executed for kernel '{args.kernel}':")
	for instName, instCnt in instcounts:
		print(f'{instCnt : 16} - {instName}')

if args.timeit:
	print(f"Execution time for kernel '{args.kernel}':")
	print('ns:', nsecs)
	print('ms:', nsecs / 1000000.0)
