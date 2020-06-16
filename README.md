# `oclude` - the OpenCL Universal Driving Environment

[![CodeFactor](https://www.codefactor.io/repository/github/zehanort/oclude/badge)](https://www.codefactor.io/repository/github/zehanort/oclude)

`oclude` is a command line tool and a Python 3 module to run and test arbitrary standalone OpenCL kernels, without the need to write hostcode or specify its arguments.

Besides simply running the OpenCL kernel, `oclude` can also:
- measure its execution time,
- count the instructions executed through an accurate and meaningful mapping from the OpenCL kernel code to the LLVM instruction set, created by using the `clang` toolkit,
- profile a specified OpenCL device.

## Current Status

The project is currently functional, with some limitations regarding mainly the complexity of the OpenCL C source code provided to it.
More specifically, successful handling of OpenCL source files that are more complicated than the [rodinia benchmark suite](https://github.com/zehanort/oclude/tree/master/tests/rodinia_kernels) is **not** guaranteed.

## System dependencies

\* *Keep in mind that proper behavior is **not** guaranteed if different versions than the ones that are listed below are used.*

At least for now, `oclude` is developed and expected to work on \*nix operating systems only.

- `python`, version >= 3.6
- `setuptools` is recommended

In case you want to use `oclude` as an OpenCL kernel driver only or measure the execution time of OpenCL kernels only:
- An `OpenCL` runtime environment. Have in mind that installing `oclude` results in also installing `pyopencl` which means that, depending on your case, this dependency may get automatically resolved.

In case you want to use `oclude` as an OpenCL kernel profiler (i.e. get LLVM instruction counts):
- The `clang` compiler (tested with version `10.0.0` that was installed along with `LLVM`)
- `g++` with `C++17` (or later) support
- `LLVM` (tested with version `10.0.0git`. You can check your version by running `llvm-config --version` in a terminal. Tested with version `3.8` and did **not** work, so my guess is that you will need something quite higher than that)
- Note: If the OpenCL kernels that you want to profile are very complex and/or large -meaning a (really) high count of instructions-, the selected OpenCL device should support the `cl_khr_int64_base_atomics` OpenCL extension. If not, `oclude` (and, more specifically, the `hostcode` component) will warn you with the following error:
```
[hostcode] WARNING: Selected device does not support the `cl_khr_int64_base_atomics` OpenCL extension!
[hostcode]          This means that instructions will not get correctly reported if they are too many!
```
Be aware that, if this extension is not supported by the selected OpenCL device, it is **not** guaranteed that the instructions reported for complex and/or large OpenCL kernels will be truthful.

## Installation

*For the time being, `oclude` is not available in `PyPI`. This is hopefully going to change in the future.*

1. `git clone` the repo and `cd` inside it:
```
git clone git@github.com:zehanort/oclude.git
cd oclude
```
2. (optional) If you need to use `oclude` as a full OpenCL kernel profiler (i.e. count `LLVM` instructions executed), you will need to build a `C++` component of `oclude`. Simply run `make` in the directory you are currently at. If any errors occur, your `g++` and/or `LLVM` versions are not compatible with `oclude`. Ignore this step; you will **not** be able to use `oclude` as a full OpenCL kernel profiler (unless you change your `g++` and/or `LLVM` versions, obviously)
3. Install `oclude` on your system or inside a virtual environment (e.g. using `venv`). From the directory you are currently at, run:
```
pip install .
```
or
```
pip install -e .
```
in case you would like to experiment with the `oclude` code.

## Usage

Everything you need to know about the different ways in which `oclude` can be used, including a full documentation of all the APIs it exports, is located in the [wiki](https://github.com/zehanort/oclude/wiki). The examples in the following sections are using the `oclude` CLI.

As a brief overview, `oclude` supports 2 different **commands**:
- the profiling of the selected **device**, and
- the execution and/or profiling of an OpenCL **kernel**.

The latter supports 2 different **modes of operation**, apart from simply executing the kernel:
- count **the LLVM instructions that were executed**, codenamed **instcounts**, and/or
- measure the **execution time**, codenamed **timeit**:

```
oclude
  ├── device
  └── kernel
        ├── instcounts
        └── timeit
```

In the `oclude` CLI, the syntax is the following:
```
$ oclude <command> <command flags>
```
Note that `command` is optional and defaults to `kernel`.

### The `device` command

An example of the `device` command in the `oclude` CLI could be the following:
```
$ oclude device -p 0 -d 0
[hostcode] Collecting profiling info for the following device:
[hostcode] Platform:	Intel(R) OpenCL HD Graphics
[hostcode] Device:	Intel(R) Gen9 HD Graphics NEO
[hostcode] Version:	OpenCL 2.1 NEO
[hostcode] Please wait, this may take a while...
Profiling info for selected OpenCL device:
        profiling overhead (time) - 0.011303499341011047
  profiling overhead (percentage) - 17.80%
                  command latency - 0.06351426243782043
  host-to-device transfer latency - 0.011074915528297424
  device-to-host transfer latency - 0.011512413620948792
device-to-device transfer latency - 0.06323426961898804
host-device bandwidth bandwidth @ 64 bytes - 0.005645181903735443 GB/s
host-device bandwidth bandwidth @ 256 bytes - 0.022125035974706695 GB/s
host-device bandwidth bandwidth @ 1024 bytes - 0.08657326467722175 GB/s
... a lot of bandwidth measurements follow ...
```

### The `kernel` command

An example of the `kernel` command in the `oclude` CLI could be the following (note that the `kernel` keyword is omitted as it is implied when absent and that, besides running the kernel, nothing else really happens):

```
$ oclude -f tests/rodinia_kernels/dwt2d/com_dwt.cl -k c_CopySrcToComponents -g 1024 -l 128
[oclude] INFO: Input file tests/rodinia_kernels/dwt2d/com_dwt.cl is not cached
[oclude] Running kernel 'c_CopySrcToComponents' from file tests/rodinia_kernels/dwt2d/com_dwt.cl
[hostcode] Using the following device:
[hostcode] Platform:    Intel(R) OpenCL HD Graphics
[hostcode] Device:      Intel(R) Gen9 HD Graphics NEO
[hostcode] Version:     OpenCL 2.1 NEO
[hostcode] Kernel name: c_CopySrcToComponents
[hostcode] Kernel arg 1: d_r (int*, global)
[hostcode] Kernel arg 2: d_g (int*, global)
[hostcode] Kernel arg 3: d_b (int*, global)
[hostcode] Kernel arg 4: cl_d_src (uchar*, global)
[hostcode] Kernel arg 5: pixels (int, private)
[hostcode] About to execute kernel with Global NDRange = 1024 and Local NDRange = 128
[hostcode] Number of executions (a.k.a. samples) to perform: 1
[hostcode] Kernel run completed successfully
```

Observe the following from the usage above:

- Firstly, an OpenCL kernel file (\*.cl) is specified with the `--file/-f` flag
- A kernel from inside this file is chosen with `--kernel/-k` (optional; if it is not used, `oclude` will inform the user of the kernels present in the input file and they will be able to choose which one to run interactively)
- The global and local OpenCL NDRanges are specified with the `--gsize/-g` and `--lsize/-l` flags, respectively. Only 1 dimension is supported, therefore these flags accept only a single positive integer.

Nothing interesting happened though... That is why the `kernel` command has 2 modes of operation.

#### Mode 1: Intstruction count

Simply use the `--inst-counts/-i` flag to instrument the kernel and count the LLVM instructions that correspond to the instructions that were actually ran by the kernel:

```
$ oclude -f tests/rodinia_kernels/dwt2d/com_dwt.cl -k c_CopySrcToComponents -g 1024 -l 128 -i
[oclude] INFO: Input file tests/rodinia_kernels/dwt2d/com_dwt.cl is cached
[oclude] INFO: Using cached instrumented file
[oclude] Running kernel 'c_CopySrcToComponents' from file tests/rodinia_kernels/dwt2d/com_dwt.cl
[hostcode] Using the following device:
[hostcode] Platform:	Intel(R) OpenCL HD Graphics
[hostcode] Device:	Intel(R) Gen9 HD Graphics NEO
[hostcode] Version:	OpenCL 2.1 NEO
[hostcode] Kernel name: c_CopySrcToComponents
[hostcode] Kernel arg 1: d_r (int*, global)
[hostcode] Kernel arg 2: d_g (int*, global)
[hostcode] Kernel arg 3: d_b (int*, global)
[hostcode] Kernel arg 4: cl_d_src (uchar*, global)
[hostcode] Kernel arg 5: pixels (int, private)
[hostcode] About to execute kernel with Global NDRange = 1024 and Local NDRange = 128
[hostcode] Number of executions (a.k.a. samples) to perform: 1
[hostcode] Collecting instruction counts...
[hostcode] Kernel run completed successfully
Instructions executed for kernel 'c_CopySrcToComponents':
           26920 - load private
           20776 - alloca
           14336 - store private
           12288 - add
           11631 - getelementptr
           11264 - mul
            8855 - store callee
            7245 - load callee
            4096 - call
            3072 - load global
            3072 - load local
            3072 - store local
            3072 - zext
            2415 - sub
            1829 - br
            1024 - ret
            1024 - icmp
```

NOTE: The output of this mode was designed to resemble that of [Oclgrind](https://github.com/jrprice/Oclgrind).

#### Mode 2: Execution time measurement

Simply use the `--time-it/-t` flag to measure the execution time of the specified kernel:

```
$ oclude -f tests/rodinia_kernels/dwt2d/com_dwt.cl -k c_CopySrcToComponents -g 1024 -l 128 -t
[oclude] INFO: Input file tests/rodinia_kernels/dwt2d/com_dwt.cl is not cached
[oclude] Running kernel 'c_CopySrcToComponents' from file tests/rodinia_kernels/dwt2d/com_dwt.cl
[hostcode] Using the following device:
[hostcode] Platform:	Intel(R) OpenCL HD Graphics
[hostcode] Device:	Intel(R) Gen9 HD Graphics NEO
[hostcode] Version:	OpenCL 2.1 NEO
[hostcode] Kernel name: c_CopySrcToComponents
[hostcode] Kernel arg 1: d_r (int*, global)
[hostcode] Kernel arg 2: d_g (int*, global)
[hostcode] Kernel arg 3: d_b (int*, global)
[hostcode] Kernel arg 4: cl_d_src (uchar*, global)
[hostcode] Kernel arg 5: pixels (int, private)
[hostcode] About to execute kernel with Global NDRange = 1024 and Local NDRange = 128
[hostcode] Number of executions (a.k.a. samples) to perform: 1
[hostcode] Collecting time profiling info...
[hostcode] Kernel run completed successfully
Time measurement info regarding the execution for kernel 'c_CopySrcToComponents' (in milliseconds):
hostcode - 1.9354820251464844
  device - 0.013415999999999999
transfer - 1.9220660251464843
```

The 2 modes of the `kernel` command can be combined to measure the execution time of the instrumented OpenCL code.

## Usage (as a Python module)

`oclude` exports its 2 commands -`device` and `kernel`- as 2 different functions:
- the `device` command is exported as the `oclude.profile_opencl_device()` function
- the `kernel` command is exported as the `oclude.profile_opencl_kernel()` function

Their complete documentation can be found in the respective [wiki page](https://github.com/zehanort/oclude/wiki/Python-module-usage).

## Limitations & known issues

1. For the time being, `oclude` instruments the OpenCL source code directly in order to count the LLVM instructions that are executed. To achieve that, a mapping between the OpenCL C source code and the LLVM bitcode [basic blocks](https://en.wikipedia.org/wiki/Basic_block) has been designed. As you may know, a 1-1 mapping between source code and basic blocks of an [IR](https://en.wikipedia.org/wiki/Intermediate_representation) is not a trivial problem, which means that many design choices had to be made. For this mapping to be properly designed, *no optimizations could be used during the parsing of the LLVM instructions to which the input source file is compiled*. This means that the instruction counts that are reported when using the `kernel` command with the `--instcounts/-i` mode of operation corresponds to the unoptimized OpenCL source code.
2. If there are certain sizes and/or values of the input arguments that may lead the specified kernel to a segfault, there are 3 different possible outcomes:
    - normal execution
    - empty output
    - execution of `oclude` hangs and you have to kill it manually
