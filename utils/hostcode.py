import pyopencl as cl
import pyopencl.cltypes as cltypes
from pyopencl.tools import get_or_register_dtype, match_dtype_to_c_struct
import pyopencl.characterize.performance as clperf
from pycparserext.ext_c_parser import OpenCLCParser
from pycparser.c_ast import Decl, Struct, Typedef, FuncDef, TypeDecl, ArrayDecl

import utils
from rvg import NumPyRVG
import numpy as np
import os
from time import time

oclude_buffer_length = len(utils.llvm_instructions)

def create_struct_type(device, struct_name, struct):
    field_decls = struct.decls
    struct_fields = []
    # iterate over struct fields
    for field_decl in field_decls:
        field_name = field_decl.name
        # field is a scalar
        if isinstance(field_decl.type, TypeDecl):
            type_name = ' '.join(field_decl.type.type.names)
            field_type = type_name if type_name != 'bool' else 'char'
            struct_fields.append((field_name, eval(f'cltypes.{field_type}')))
        # field is an array (with defined size TODO: OR IDENTIFIER!!!)
        elif isinstance(field_decl.type, ArrayDecl):
            raise NotImplementedError('arrays as struct fields are not supported yet')
            struct_fields.append((field_name, create_array_type(field_name, field_decl)))
        else:
            raise NotImplementedError(f'field `{field_name}` of struct `{struct_name}` has a type that can not be understood')

    # register struct
    struct_dtype = np.dtype(struct_fields)
    struct_dtype, _ = match_dtype_to_c_struct(device, struct_name, struct_dtype)
    struct_dtype = get_or_register_dtype(struct_name, struct_dtype)
    return struct_dtype

def run_kernel(kernel_file_path, kernel_name, GSIZE, WGROUPS, instcounts, timeit, platform_id, device_id, verbose):
    '''
    The hostcode wrapper function
    Essentially, it is nothing more than an OpenCL template hostcode,
    but it is the heart of oclude
    '''

    interact = utils.Interactor(__file__.split(os.sep)[-1])
    interact.set_verbosity(verbose)

    ### step 1: get OpenCL platform, device and context, ###
    ### build the kernel program and create a queue      ###
    # TODO: some OpenCL-related checks
    platform = cl.get_platforms()[platform_id]
    interact(f'Using platform: {platform.name}')

    device = platform.get_devices()[device_id]
    interact(f'Using device: {device.name} (device OpenCL version: {device.version.strip()})')

    context = cl.Context([device])
    with open(kernel_file_path, 'r') as kernel_file:
        program = cl.Program(context, kernel_file.read()).build()

    if timeit:
        queue = cl.CommandQueue(context, properties=cl.command_queue_properties.PROFILING_ENABLE)
    else:
        queue = cl.CommandQueue(context)

    ### step 2: get kernel arg info ###
    interact(f'Kernel name: {kernel_name}')

    [kernel] = filter(lambda k : k.function_name == kernel_name, program.all_kernels())
    nargs = kernel.get_info(cl.kernel_info.NUM_ARGS)

    args = []

    for idx in range(nargs):
        kernel_arg_name = kernel.get_arg_info(idx, cl.kernel_arg_info.NAME)
        is_oclude_hidden_buffer = kernel_arg_name in [utils.hidden_counter_name_local, utils.hidden_counter_name_global]
        if not is_oclude_hidden_buffer:
            interact(f'Kernel arg {idx + 1}: ', nl=False)
        kernel_arg_type_name = kernel.get_arg_info(idx, cl.kernel_arg_info.TYPE_NAME)
        kernel_arg_address_qualifier = cl.kernel_arg_address_qualifier.to_string(
            kernel.get_arg_info(idx, cl.kernel_arg_info.ADDRESS_QUALIFIER)
        ).lower()
        if not is_oclude_hidden_buffer:
            interact(f'{kernel_arg_name} ({kernel_arg_type_name}, {kernel_arg_address_qualifier})', prompt=False)
        args.append((kernel_arg_name, kernel_arg_type_name, kernel_arg_address_qualifier))

    ### step 3: collect arg types ###
    arg_types = {}
    parser = None
    ast = None
    typedefs = {}
    structs = {}

    for kernel_arg_name, kernel_arg_type_name, _ in args:

        argtype_base = kernel_arg_type_name.split('*')[0]

        try:
            # it is a normal OpenCL type
            arg_types[kernel_arg_name] = eval('cltypes.' + argtype_base)

        except AttributeError:
            # it is a struct (lazy evaluation of structs)
            if parser is None:
                parser = OpenCLCParser()
                cmdout, _ = interact.run_command(None, utils.utils.preprocessor, kernel_file_path)
                kernel_source = '\n'.join(filter(lambda line : line.strip() and not line.startswith('#'), cmdout.splitlines()))
                ast = parser.parse(kernel_source)

                for ext in ast.ext:

                    ### typedefs ###
                    if isinstance(ext, Typedef):
                        if isinstance(ext.type.type, Struct):
                            # typedefed struct (new)
                            if ext.type.type.decls is not None:
                                typedefs[ext.name] = create_struct_type(device, ext.name, ext.type.type)
                            # typedefed struct (already seen it)
                            else:
                                previous_name = 'struct ' + ext.type.type.name
                                new_name = ext.name
                                typedefs[new_name] = structs[previous_name]
                        # simple typedef (not a struct)
                        else:
                            previous_name = ' '.join(ext.type.type.names)
                            new_name = ext.name
                            typedefs[new_name] = ext.type

                    ### struct declarations ###
                    elif isinstance(ext, Decl) and isinstance(ext.type, Struct):
                        name = 'struct ' + ext.type.name
                        structs[name] = create_struct_type(device, ext.type.name, ext.type)

            try:
                arg_types[kernel_arg_name] = structs[argtype_base]
            except KeyError:
                arg_types[kernel_arg_name] = typedefs[argtype_base]

    ### step 4: create argument buffers ###
    rand = NumPyRVG(limit=GSIZE)
    arg_hostbufs = []
    arg_bufs = []
    # will be needed to set scalar args
    which_are_scalar = []
    mem_flags = cl.mem_flags.READ_WRITE | cl.mem_flags.COPY_HOST_PTR
    hidden_global_hostbuf = None
    hidden_global_buf = None

    for (argname, argtypename, argaddrqual), argtype in zip(args, arg_types.values()):

        # special handling of oclude hidden buffers
        if argname == utils.hidden_counter_name_local:
            which_are_scalar.append(None)
            arg_bufs.append(cl.LocalMemory(oclude_buffer_length * argtype(0).itemsize))
            continue
        if argname == utils.hidden_counter_name_global:
            which_are_scalar.append(None)
            hidden_global_hostbuf = np.zeros(oclude_buffer_length * WGROUPS, dtype=argtype)
            arg_hostbufs.append(hidden_global_hostbuf)
            hidden_global_buf = cl.Buffer(context, mem_flags, hostbuf=hidden_global_hostbuf)
            arg_bufs.append(hidden_global_buf)
            continue

        argtypename_split = argtypename.split('*')
        argtypename_base = argtypename_split[0]
        arg_is_local = argaddrqual == 'local'
        # argument is scalar
        if len(argtypename_split) == 1:
            which_are_scalar.append(argtype)
            val = rand(argtype)
            arg_hostbufs.append(val)
            arg_bufs.append(val if not arg_is_local else cl.LocalMemory(val.itemsize))
        # argument is buffer
        else:
            which_are_scalar.append(None)
            val = rand(argtype, GSIZE)
            arg_hostbufs.append(val)
            arg_bufs.append(
                cl.Buffer(context, mem_flags, hostbuf=val) if not arg_is_local else cl.LocalMemory(len(val) * val.dtype.itemsize)
            )

    ### step 5: set kernel arguments and run it!
    kernel.set_scalar_arg_dtypes(which_are_scalar)
    LSIZE = GSIZE//WGROUPS
    interact(f'Enqueuing kernel with Global NDRange = {GSIZE} and Local NDRange = {LSIZE}')

    time_start = time()
    time_finish = None

    event = kernel(queue, (GSIZE,), (GSIZE//WGROUPS,), *arg_bufs)
    interact('Kernel run completed successfully')

    if timeit:
        event.wait()
        time_finish = time()

    queue.finish()

    ### step 6: read back the results and report them if requested
    results = {
        'instcounts': None,
        'timeit': {
            'kernel': None,
            'general': None
        }
    }

    if instcounts:
        interact('Collecting instruction counts')
        global_counter = np.empty_like(hidden_global_hostbuf)
        cl.enqueue_copy(queue, global_counter, hidden_global_buf)

        final_counter = [0 for _ in range(oclude_buffer_length)]
        for i in range(oclude_buffer_length):
            for j in range(WGROUPS):
                final_counter[i] += global_counter[i + j * oclude_buffer_length]

        results['instcounts'] = {
            k: v for k, v in sorted(dict(zip(utils.llvm_instructions, final_counter)).items(), key=lambda item: item[1], reverse=True)
        }

    if timeit:
        interact('Collecting time profiling info, please wait')
        # kernel profiling
        hostcode_time_elapsed = (time_finish - time_start) * 1000
        device_time_elapsed = (event.profile.end - event.profile.start) * 1e-6

        # general profiling
        prof_overhead, latency = clperf.get_profiling_overhead(context)
        h2d_latency = clperf.transfer_latency(queue, clperf.HostToDeviceTransfer) * 1000
        d2h_latency = clperf.transfer_latency(queue, clperf.DeviceToHostTransfer) * 1000
        d2d_latency = clperf.transfer_latency(queue, clperf.DeviceToDeviceTransfer) * 1000

        results['timeit']['kernel'] = {
            'hostcode': hostcode_time_elapsed,
            'device': device_time_elapsed,
            'transfer': hostcode_time_elapsed - device_time_elapsed
        }

        results['timeit']['general'] = {
            'profiling overhead (time)': prof_overhead * 1000,
            'profiling overhead (percentage)': f'{(100 * prof_overhead / latency):.2f}%',
            'command latency': latency * 1000,
            'host-to-device transfer latency': h2d_latency,
            'device-to-host transfer latency': d2h_latency,
            'device-to-device transfer latency': d2d_latency
        }

    return results
