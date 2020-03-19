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
    help='the name of the kernel to run from the input file'
    # required=True
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

###############################
### MAIN FUNCTION OF OCLUDE ###
###############################
def run():

    args = parser.parse_args()

    interact = utils.Interactor(__file__.split(os.sep)[-1])
    interact.set_verbosity(args.verbose)

    # some sanity checks
    if not os.path.exists(utils.cfg.clcHeaderFile) or not os.path.exists(utils.cfg.libclcIncludePath):
        interact('ERROR: paths to libclc header file and/or include directory are invalid.')
        interact('Have you set them correctly before running oclude?')
        interact('If not, they are located in the file ' + os.path.abspath(os.path.join('utils', 'cfg', '__init__.py')))
        exit(1)

    if not os.path.exists(args.infile):
        interact(f'ERROR: Input file {args.infile} does not exist.')
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

    ### STEP 0: check our database for this file  ###
    ### if the file exists, just run it           ###
    ### if the file does not exist, instrument it ###
    ### if the database does not exist, create it ###

    cache = utils.CachedFiles(args.instcounts)

    if cache.exists() and cache.file_is_cached(args.infile):
        interact(f'INFO: Input file {args.infile} is cached; working with it')
        infile = cache.get_file(args.infile)

    else:

        if not cache.exists():
            interact('INFO: Cached files directory does not exist, creating it... ', nl=False)
            cache.create()
            interact('done', prompt=False)

        else: # else cache exists but does not have the input file
            interact(f'INFO: Input file {args.infile} is not cached; need to instrument and cache it')

        infile = cache.create_file(args.infile)

        ### STEP 1: instrument input source file ###
        ###  the final code ends up in tempfile  ###
        interact('Instrumenting source code')
        if args.instcounts:
            file_kernels = utils.instrument_file(infile, args.verbose)
        else:
            file_kernels = cache.find_file_kernels(infile)

        cache.cache_file_kernels(infile, file_kernels)

    # a last sanity check
    file_kernels = cache.get_file_kernels(infile)
    if not args.kernel or args.kernel not in file_kernels:
        if args.kernel:
            interact(f"ERROR: No kernel function named '{args.kernel}' exists in file '{args.infile}'")
        interact(f"A list of the kernels that exist in file '{args.infile}':")
        for i, kernel in enumerate(file_kernels, 1):
            interact(f'\t{i}. {kernel}')
        # input file contains only one kernel
        if len(file_kernels) == 1:
            interact('Do you want to run the above kernel? [Y/n] ', nl=False)
            if input() == 'n':
                exit(0)
            else:
                inp = 0
        # input file contains > 1 kernels
        else:
            interact('Do you want to run one of the above? If yes, type the number on its left. If no, just hit <Enter>: ', nl=False)
            inp = input()
            if not inp:
                exit(0)
            else:
                inp = int(inp) - 1
                if not 0 <= inp < len(file_kernels):
                    interact(f'Should have chosen between 1 and {len(file_kernels)}. Please try again')
                    exit(1)
        args.kernel = file_kernels[inp]
        interact(f"Continuing with kernel '{args.kernel}'")

    ### STEP 2: run the kernel ###
    hostcodeWrapper = os.path.join(utils.bindir, 'hostcode-wrapper')
    hostcodeWrapperFlags = [
        infile,
        args.kernel,
        str(args.size),
        str(args.work_groups),
        'y' if args.instcounts else 'n',
        'y' if args.timeit else 'n',
        str(args.platform),
        str(args.device)
    ]

    cmdout, cmderr = interact.run_command(f'Running kernel {args.kernel} from file {args.infile}', hostcodeWrapper, *hostcodeWrapperFlags)

    interact(cmderr, prompt=False, nl=False)
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
