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

    errors = []
    command = f'oclude {kernelfilepath} -k {kernel} -g {GSIZE} -l {LSIZE} -i'
    output, error, retcode = run_command(command)

    # skip empty output tests to differentiate them from other failures
    if len(output.splitlines()) == 1:
        pytest.skip('empty output')

    assert output
    assert retcode == 0
