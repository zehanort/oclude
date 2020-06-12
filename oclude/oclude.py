import argparse
import os
from functools import reduce
from collections import Counter
import operator

import oclude.utils as utils

# define the arguments of oclude
parser = argparse.ArgumentParser(
    description='oclude - the OpenCL universal driving environment',
    formatter_class=argparse.RawTextHelpFormatter
)

parser.add_argument('command',
    type=str,
    nargs='?',
    choices=['kernel', 'device'],
    help='''oclude supports the following commands:

   kernel    Profile an OpenCL kernel from a given source file
             (default if <command> is ommited)
   device    Profile the selected OpenCL device
             (only -p and -d flags are taken into consideration)''',
    default='kernel'
)

parser.add_argument('-f', '--file',
    type=str,
    help='the *.cl file with the OpenCL kernel(s)'
)

parser.add_argument('-k', '--kernel',
    type=str,
    help='the name of the kernel to run from the input file'
)

parser.add_argument('-g', '--gsize',
    type=int,
    help='The global NDRange, i.e. the size of the buffer arguments of the kernel'
)

parser.add_argument('-l', '--lsize',
    type=int,
    help='The local NDRange, i.e. the number of work items in a work group'
)

parser.add_argument('-p', '--platform',
    type=int,
    help='the index of the OpenCL platform to use (default: 0)',
    default=0,
    dest='platform_id'
)

parser.add_argument('-d', '--device',
    type=int,
    help='the index of the OpenCL device to use (default: 0)',
    default=0,
    dest='device_id'
)

parser.add_argument('-s', '--samples',
    type=int,
    help='number of times to execute the given kernel (note that each execution is initialized with different values)',
    default=1
)

parser.add_argument('-v', '--verbose',
    help='toggle verbose output (default: false)',
    action='store_true',
    default=False
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

# cache flags #
parser.add_argument('--clear-cache',
    help='remove every cached info (irreversible)',
    dest='clear_cache',
    action='store_true'
)

parser.add_argument('--ignore-cache',
    help='do not use (possibly) cached info regarding the provided kernel file',
    dest='ignore_cache',
    action='store_true'
)

parser.add_argument('--no-cache-warnings',
    help='suppress cache-related warnings (e.g. cache too large)',
    dest='no_cache_warnings',
    action='store_true'
)

def profile_opencl_kernel(file, kernel,
                          gsize, lsize,
                          platform_id=0, device_id=0,
                          samples=1,
                          instcounts=False, timeit=False,
                          verbose=False,
                          clear_cache=False, ignore_cache=False, no_cache_warnings=False):

    interact = utils.Interactor(__file__.split(os.sep)[-1])
    interact.set_verbosity(verbose)

    # some sanity checks
    if not lsize or not gsize:
        interact(f'ERROR: arguments -g/--gsize and -l/--lsize are required')
        exit(1)

    if not os.path.exists(file):
        interact(f'ERROR: Input file {file} does not exist.')
        exit(1)

    if instcounts and timeit:
        interact('WARNING: Instruction count and execution time measurement were both requested.')
        interact('This will result in the time measurement of the instrumented kernel and not the original.')

    ### STEP 1: cache checking (if needed) ###
    ##########################################
    #   1. was any of the flags below used?
    #       instcounts: Is the instrumented version of the file cached?
    #           YES: use it
    #           NO: go on to instrumentation, remember to cache it when done
    #       timeit: No need to do something
    #   2. check if cache knows the file kernels (this whole step should be done transparently, inside cache class)
    #       YES: get them and:
    #           a. user specified a kernel: check if it exists in the file (could fail)
    #           b. user did not specify a kernel: prompt them
    #       NO: find them, and go to YES
    ##########################################

    cache = utils.CachedFiles()

    if cache.size > 10 * 1024 * 1024 and not no_cache_warnings:
        interact('WARNING: Cache size exceeds 10 MiB, which is a lot. Consider running oclude with `--clear-cache`')

    if clear_cache:
        interact('INFO: Clearing cache')
        cache.clear()

    is_cached = False
    if ignore_cache:
        interact('INFO: Ignoring cache')
    else:
        is_cached = cache.file_is_cached(file)
        interact(f"INFO: Input file {file} is {'' if is_cached else 'not '}cached")

    # step 1.1
    if instcounts:
        instrumented_file = cache.get_name_of_instrumented_file(file)
        if is_cached and not ignore_cache:
            interact('INFO: Using cached instrumented file')
        else:
            interact('Instrumenting source file')
            cache.copy_file_to_cache(file)
            utils.instrument_file(instrumented_file, verbose)
    else:
        instrumented_file = file

    # step 1.2
    file_kernels = cache.get_file_kernels(file)
    if not kernel or kernel not in file_kernels:
        if kernel:
            interact(f"ERROR: No kernel function named '{kernel}' exists in file '{file}'")
        interact(f"A list of the kernels that exist in file '{file}':")
        for i, kernel_name in enumerate(file_kernels, 1):
            interact(f'\t{i}. {kernel_name}')
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
        kernel = file_kernels[inp]
        interact(f"Continuing with kernel '{kernel}'")

    ### STEP 2: run the kernel ###
    interact(f"Running kernel '{kernel}' from file {file}")
    kernel_run_results = utils.run_kernel(
        instrumented_file, kernel,
        gsize, lsize,
        platform_id, device_id,
        samples,
        instcounts, timeit,
        verbose
    )
    return {
        'original file':     file,
        'instrumented file': instrumented_file if instrumented_file != file else None,
        'kernel':            kernel,
        'results':           kernel_run_results
    }

###############################
### MAIN FUNCTION OF OCLUDE ###
###############################
def run():

    args = parser.parse_args()

    interact = utils.Interactor(__file__.split(os.sep)[-1])
    interact.set_verbosity(args.verbose)

    if args.command == 'device':
        device_prof_results = utils.profile_opencl_device(args.platform_id, args.device_id, args.verbose)
        indent = max(len(profiling_category) for profiling_category in device_prof_results.keys())
        print('Profiling info for selected OpenCL device:')
        for profiling_category, profiling_info in device_prof_results.items():
            if isinstance(profiling_info, dict):
                for k, v in profiling_info.items():
                    category_name = f'{profiling_category} bandwidth @ {k}'
                    print(f'{category_name:>{indent}} - {v}')
            else:
                print(f'{profiling_category:>{indent}} - {profiling_info}')
        exit(0)

    args_dict = vars(args)
    del args_dict['command']
    results = profile_opencl_kernel(**args_dict)

    ### STEP 3: dump an oclgrind-like output (if requested by user) ###

    # reduce all runs to a single dict of results
    selected_kernel = results['kernel']
    results = results['results']
    reduced_results = {}
    samples = args.samples

    if args.instcounts:
        if samples > 1:
            interact(f'Calculating average instruction counts over {samples} samples... ', nl=False)
        reduced_results['instcounts'] = dict(
            reduce(operator.add, map(Counter, map(lambda x : x['instcounts'], results)))
        )
        reduced_results['instcounts'] = {
            k : int(v) // (samples if samples > 0 else 1) for k, v in reduced_results['instcounts'].items()
        }
        if samples > 1:
            interact('done', prompt=False)

    if args.timeit:
        if samples > 1:
            interact(f'Calculating average time profiling info over {samples} samples... ', nl=False)
        reduced_results['timeit'] = dict(
            reduce(operator.add, map(Counter, map(lambda x : x['timeit'], results)))
        )
        reduced_results['timeit'] = {
            k : v / (samples if samples > 0 else 1) for k, v in reduced_results['timeit'].items()
        }
        if samples > 1:
            interact('done', prompt=False)

    # in the CLI of oclude, we only need the average of the samples
    results = reduced_results

    if args.instcounts:
        print(f"Instructions executed for kernel '{selected_kernel}'" + (' (average):' if args.samples > 1 else ':'))
        for instname, instcount in sorted(results['instcounts'].items(), key=lambda item : item[1], reverse=True):
            if instcount != 0:
                print(f'{instcount:16} - {instname}')

    if args.timeit:
        kernel_results = results['timeit']
        indent = max(len(timing_scope) for timing_scope in kernel_results.keys())
        print(f"Time measurement info regarding the execution for kernel '{selected_kernel}' ("
                + ('average, ' if args.samples > 1 else '') + "in milliseconds):")
        for timing_scope, time_elapsed in kernel_results.items():
            print(f'{timing_scope:>{indent}} - {time_elapsed}')
