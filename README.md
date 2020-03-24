# `oclude` - the OpenCL Universal Driving Environment

[![CodeFactor](https://www.codefactor.io/repository/github/zehanort/oclude/badge)](https://www.codefactor.io/repository/github/zehanort/oclude)

`oclude` is a command line tool to run and test arbitrary standalone OpenCL kernels, without the need to write hostcode or specify its arguments.

Besides simply running the OpenCL kernel, `oclude` can also:
- measure its execution time,
- count the instructions executed through an accurate and meaningful mapping from the OpenCL kernel code to the LLVM instruction set, created by using the `clang` toolkit.

## Current Status

The project is under (rather heavy) development and should not be considered functional yet.

Further documentation will be added when the project reaches its BETA version.

## System dependencies

(specifics to be added soon, roughly `LLVM`, `clang` and, obviously, an OpenCL runtime environment)

## Python dependencies

(specifics to be added soon, but no need to worry, installing `oclude` from `pip` will take care of these for you - that is, when its author feels confident enough to upload it)

## Modes of operation

`oclude` can be used to simply run an OpenCL kernel, with nothing else actually happening. Explaining the usage below (you can see all flags with `oclude -h`)
- Firstly, an OpenCL kernel file (\*.cl) must be specified
- A kernel from inside this file is chosen with `-k` (optional; if it is not used, `oclude` will inform the user of the kernels present in the input file and they will be able to choose which one to run interactively)
- Specify the OpenCL NDRange with `-s` and the number of work groups with `-w`

```
$ oclude tests/dwt2d/com_dwt.cl -k c_CopySrcToComponents -s 1024 -w 8
[oclude] INFO: Input file tests/dwt2d/com_dwt.cl is cached
[oclude] Running kernel c_CopySrcToComponents from file tests/dwt2d/com_dwt.cl
```

Nothing interesting happened though... That is why `oclude` has 2 modes of operation:

### Mode 1: Execution time measurement

Simply use the flag `--time-it` or `-t` to measure the execution time of the specified kernel:

```
$ oclude tests/dwt2d/com_dwt.cl -k c_CopySrcToComponents -s 1024 -w 8 -t
[oclude] INFO: Input file tests/dwt2d/com_dwt.cl is cached
[oclude] Running kernel c_CopySrcToComponents from file tests/dwt2d/com_dwt.cl
Execution time for kernel 'c_CopySrcToComponents':
ns: 8166.0
ms: 0.008166
```

### Mode 2: Intstruction count

Simply use the flag `--inst-counts` or `-i` to instrument the kernel and count the LLVM instructions that correspond to the instructions that were actually ran by the kernel:

```
$ oclude tests/dwt2d/com_dwt.cl -k c_CopySrcToComponents -s 1024 -w 8 -i
[oclude] INFO: Input file tests/dwt2d/com_dwt.cl is cached
[oclude] INFO: Using cached instrumented file
[oclude] Running kernel c_CopySrcToComponents from file tests/dwt2d/com_dwt.cl
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
