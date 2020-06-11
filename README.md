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
2. (optional) If you need to use `oclude` as a full OpenCL kernel profiler (i.e. count `LLVM` instructions executed), you will need to build a `C++` component of `oclude`. Simply run `make` in the directory you are currently at. If any errors occur, your `g++` and/or `LLVM` versions are not compatible with `oclude`. Ignore this step; you want be able to use `oclude` as a full OpenCL kernel profiler (unless you change your `g++` and/or `LLVM` versions, obviously)
3. Install `oclude` on your system or inside a virtual environment (e.g. using `venv`). From the directory you are currently at, run:
```
pip install .
```
or
```
pip install -e .
```
in case you would like to experiment with the `oclude` code.

## Modes of operation

\* *The modes of operation will be presented using the `CLI` of `oclude`. For its Python 3 module usage, see next section.*

\*\* *WARNING: This section is **DEPRECATED**; will be updated ASAP*

`oclude` can be used to simply run an OpenCL kernel, with nothing else actually happening. Explaining the usage below (you can see all flags with `oclude -h`)
- Firstly, an OpenCL kernel file (\*.cl) must be specified
- A kernel from inside this file is chosen with `-k` (optional; if it is not used, `oclude` will inform the user of the kernels present in the input file and they will be able to choose which one to run interactively)
- Specify the OpenCL NDRange with `-s` and the number of work groups with `-w`

```
$ oclude tests/dwt2d/com_dwt.cl -k c_CopySrcToComponents -s 1024 -w 8
[oclude] INFO: Input file tests/dwt2d/com_dwt.cl is cached
[oclude] Running kernel c_CopySrcToComponents from file tests/dwt2d/com_dwt.cl
[hostcode-wrapper] Using platform: Intel(R) OpenCL HD Graphics
[hostcode-wrapper] Using device: Intel(R) Gen9 HD Graphics NEO (device OpenCL version: OpenCL 2.1 NEO )
[hostcode-wrapper] Kernel name: c_CopySrcToComponents
[hostcode-wrapper] Kernel arg 0: d_r (int*, global)
[hostcode-wrapper] Kernel arg 1: d_g (int*, global)
[hostcode-wrapper] Kernel arg 2: d_b (int*, global)
[hostcode-wrapper] Kernel arg 3: cl_d_src (uchar*, global)
[hostcode-wrapper] Kernel arg 4: pixels (int, private)
[hostcode-wrapper] Enqueuing kernel with Global NDRange = 1024 and Local NDRange = 128
[oclude] Kernel run completed successfully
```

Nothing interesting happened though... That is why `oclude` has 2 modes of operation:

### Mode 1: Execution time measurement

Simply use the flag `--time-it` or `-t` to measure the execution time of the specified kernel:

```
$ oclude tests/dwt2d/com_dwt.cl -k c_CopySrcToComponents -s 1024 -w 8 -t
[oclude] INFO: Input file tests/dwt2d/com_dwt.cl is cached
[oclude] Running kernel c_CopySrcToComponents from file tests/dwt2d/com_dwt.cl
[hostcode-wrapper] Using platform: Intel(R) OpenCL HD Graphics
[hostcode-wrapper] Using device: Intel(R) Gen9 HD Graphics NEO (device OpenCL version: OpenCL 2.1 NEO )
[hostcode-wrapper] Kernel name: c_CopySrcToComponents
[hostcode-wrapper] Kernel arg 0: d_r (int*, global)
[hostcode-wrapper] Kernel arg 1: d_g (int*, global)
[hostcode-wrapper] Kernel arg 2: d_b (int*, global)
[hostcode-wrapper] Kernel arg 3: cl_d_src (uchar*, global)
[hostcode-wrapper] Kernel arg 4: pixels (int, private)
[hostcode-wrapper] Enqueuing kernel with Global NDRange = 1024 and Local NDRange = 128
[oclude] Kernel run completed successfully
Execution time for kernel 'c_CopySrcToComponents':
ns: 8083.0
ms: 0.008083
```

### Mode 2: Intstruction count

Simply use the flag `--inst-counts` or `-i` to instrument the kernel and count the LLVM instructions that correspond to the instructions that were actually ran by the kernel:

```
$ oclude tests/dwt2d/com_dwt.cl -k c_CopySrcToComponents -s 1024 -w 8 -i
[oclude] INFO: Input file tests/dwt2d/com_dwt.cl is cached
[oclude] INFO: Using cached instrumented file
[oclude] Running kernel c_CopySrcToComponents from file tests/dwt2d/com_dwt.cl
[hostcode-wrapper] Using platform: Intel(R) OpenCL HD Graphics
[hostcode-wrapper] Using device: Intel(R) Gen9 HD Graphics NEO (device OpenCL version: OpenCL 2.1 NEO )
[hostcode-wrapper] Kernel name: c_CopySrcToComponents
[hostcode-wrapper] Kernel arg 0: d_r (int*, global)
[hostcode-wrapper] Kernel arg 1: d_g (int*, global)
[hostcode-wrapper] Kernel arg 2: d_b (int*, global)
[hostcode-wrapper] Kernel arg 3: cl_d_src (uchar*, global)
[hostcode-wrapper] Kernel arg 4: pixels (int, private)
[hostcode-wrapper] Enqueuing kernel with Global NDRange = 1024 and Local NDRange = 128
[oclude] Kernel run completed successfully
Instructions executed for kernel 'c_CopySrcToComponents':
            6144 - add
            6144 - getelementptr
            6144 - sext
            4096 - call
            3072 - mul
            3072 - load private
            3072 - load global
            3072 - store private
            3072 - zext
            2048 - br
            2048 - trunc
            1024 - icmp
```

NOTE: The output of this mode was designed to resemble that of [Oclgrind](https://github.com/jrprice/Oclgrind).
