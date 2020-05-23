import pytest
import os
import subprocess as sp

### SOME GLOBALS ###
testdir = os.path.dirname(os.path.abspath(__file__))
SIZE = 1024
WORK_GROUPS = 8

def run_command(command):
    cmdout = sp.run(command.split(), stdout=sp.PIPE, stderr=sp.PIPE)
    return cmdout.stdout.decode('ascii'), cmdout.stderr.decode('ascii'), cmdout.returncode

@pytest.yield_fixture(scope='session', autouse=True)
def ensure_consistent_cache_state():

    cachedir = os.path.join(os.path.split(os.path.dirname(os.path.abspath(__file__)))[0], 'utils', '.cache')
    files_before = os.listdir(cachedir)

    yield # run test session #

    for filename in filter(lambda f : f not in files_before, os.listdir(cachedir)):
        file_path = os.path.join(cachedir, filename)
        try:
            os.unlink(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

def run_kernel(kernelfile, kernel):

    kernelfilepath = os.path.join(testdir, kernelfile)

    errors = []
    command = f'oclude {kernelfilepath} -k {kernel} -s {SIZE} -w {WORK_GROUPS} -i'
    output, error, retcode = run_command(command)

    # skip empty output tests to differentiate them from other failures
    if len(output.splitlines()) == 1:
        pytest.skip('empty output')

    assert output
    assert retcode == 0
