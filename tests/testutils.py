import pytest
import os
import subprocess as sp

### SOME GLOBALS ###
testdir = os.path.dirname(os.path.abspath(__file__))
GSIZE = 1024
LSIZE = 128

def run_command(command):
    cmdout = sp.run(command.split(), stdout=sp.PIPE, stderr=sp.PIPE)
    return cmdout.stdout.decode('ascii'), cmdout.stderr.decode('ascii'), cmdout.returncode

def run_kernel(kernelfile, kernel):
    kernelfilepath = os.path.join(testdir, kernelfile)
    command = f'oclude kernel -f {kernelfilepath} -k {kernel} -g {GSIZE} -l {LSIZE} -i'
    output, error, retcode = run_command(command)

    # skip empty output tests to differentiate them from other failures
    if len(output.splitlines()) == 1:
        pytest.skip('empty output')

    assert output
    assert retcode == 0

def run_kernel_from_module(kernelfile, kernel):
    from oclude import profile_opencl_kernel
    from oclude.utils.constants import llvm_instructions
    kernelfilepath = os.path.join(testdir, kernelfile)

    # case 1: neither instcounts nor timeit, samples = 1
    res = profile_opencl_kernel(file=kernelfilepath, kernel=kernel, gsize=1024, lsize=128)
    assert all(x in res for x in ['original file', 'instrumented file', 'kernel', 'results'])
    assert res['results'] is None

    # case 2: neither instcounts nor timeit, samples > 1
    res = profile_opencl_kernel(file=kernelfilepath, kernel=kernel, gsize=1024, lsize=128, samples=10)
    assert all(x in res for x in ['original file', 'instrumented file', 'kernel', 'results'])
    assert res['results'] is None

    # case 3: only instcounts, samples = 1
    res = profile_opencl_kernel(file=kernelfilepath, kernel=kernel, gsize=1024, lsize=128, instcounts=True)
    assert all(x in res for x in ['original file', 'instrumented file', 'kernel', 'results'])
    assert len(res['results']) == 1
    assert sorted(list(res['results'][0]['instcounts'].keys())) == sorted(llvm_instructions)
    assert all(isinstance(x, int) for x in res['results'][0]['instcounts'].values())

    # case 4: only timeit, samples = 1
    res = profile_opencl_kernel(file=kernelfilepath, kernel=kernel, gsize=1024, lsize=128, timeit=True)
    assert all(x in res for x in ['original file', 'instrumented file', 'kernel', 'results'])
    assert len(res['results']) == 1
    assert all(x in res['results'][0]['timeit'] for x in ['hostcode', 'device', 'transfer'])

    # case 5: both instcounts and timeit, samples = 1
    res = profile_opencl_kernel(file=kernelfilepath, kernel=kernel, gsize=1024, lsize=128, instcounts=True, timeit=True)
    assert all(x in res for x in ['original file', 'instrumented file', 'kernel', 'results'])
    assert len(res['results']) == 1
    assert sorted(list(res['results'][0]['instcounts'].keys())) == sorted(llvm_instructions)
    assert all(isinstance(x, int) for x in res['results'][0]['instcounts'].values())
    assert all(x in res['results'][0]['timeit'] for x in ['hostcode', 'device', 'transfer'])

    # case 6: both instcounts and timeit, samples > 1
    res = profile_opencl_kernel(file=kernelfilepath, kernel=kernel, gsize=1024, lsize=128, instcounts=True, timeit=True, samples=10)
    assert all(x in res for x in ['original file', 'instrumented file', 'kernel', 'results'])
    assert len(res['results']) == 10
    for results in res['results']:
        assert sorted(list(results['instcounts'].keys())) == sorted(llvm_instructions)
        assert all(isinstance(x, int) for x in results['instcounts'].values())
        assert all(x in results['timeit'] for x in ['hostcode', 'device', 'transfer'])
