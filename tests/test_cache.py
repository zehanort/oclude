import pytest
import os, shutil
import subprocess as sp
from tempfile import gettempdir

### SOME GLOBALS ###
testdir = os.path.dirname(os.path.abspath(__file__))
cachedir = os.path.join(os.path.split(os.path.dirname(os.path.abspath(__file__)))[0], 'utils', '.cache')
SIZE = 1024
WORK_GROUPS = 8

src1 = '''
__kernel void vadd(__global float* a, __constant float* b, __global float* c, const unsigned int count)
{
    int i = get_global_id(0);
    if(i < count) c[i] = a[i] + b[i];
}'''

src2 = '''
__kernel void vmul(__global float* a, __constant float* b, __global float* c, const unsigned int count)
{
    int i = get_global_id(0);
    if(i < count) c[i] = a[i] * b[i];
}'''

tmptestdir1 = os.path.join(testdir, 'tmptestdir1')
tmptestdir2 = os.path.join(testdir, 'tmptestdir2')

kernel1 = os.path.join(tmptestdir1, 'same_name.cl')
kernel2 = os.path.join(tmptestdir2, 'same_name.cl')

@pytest.yield_fixture(scope='session', autouse=True)
def ensure_consistent_cache_state():

    tmpdir = gettempdir()
    files_moved = []
    for filename in os.listdir(cachedir):
        file_path_from = os.path.join(cachedir, filename)
        file_path_to = os.path.join(tmpdir, filename)
        try:
            shutil.move(file_path_from, file_path_to)
        except Exception as e:
            print('Failed to move %s to %s. Reason: %s' % (file_path_from, file_path_to, e))
        files_moved.append((file_path_to, file_path_from))

    yield # run test session #

    # clear cache
    for filename in os.listdir(cachedir):
        file_path = os.path.join(cachedir, filename)
        try:
            os.unlink(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

    # restore previous cache files
    for file_path_from, file_path_to in files_moved:
        try:
            shutil.move(file_path_from, file_path_to)
        except Exception as e:
            print('Failed to move %s to %s. Reason: %s' % (file_path_from, file_path_to, e))

@pytest.yield_fixture(autouse=True)
def handle_test_files():
    try:
        shutil.rmtree(tmptestdir1)
        shutil.rmtree(tmptestdir2)
    except:
        pass

    os.mkdir(tmptestdir1)
    os.mkdir(tmptestdir2)

    with open(kernel1, 'w') as f:
        f.write(src1)
    with open(kernel2, 'w') as f:
        f.write(src2)

    yield ### run test ###

    shutil.rmtree(tmptestdir1)
    shutil.rmtree(tmptestdir2)
    os.remove(os.path.join(testdir, os.path.join(cachedir, 'instr_same_name.cl')))
    os.remove(os.path.join(testdir, os.path.join(cachedir, 'same_name.cl.digest')))
    os.remove(os.path.join(testdir, os.path.join(cachedir, 'same_name.cl.kernels')))

def test_kernel_files_same_name():

    errors = []

    # run first kernel
    cmdout1 = sp.run(f"oclude {kernel1} -s {SIZE} -w {WORK_GROUPS} -k vadd", stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
    output1 = cmdout1.stdout.decode('ascii')
    error1 = cmdout1.stderr.decode('ascii')

    # run second kernel
    cmdout2 = sp.run(f"oclude {kernel2} -s {SIZE} -w {WORK_GROUPS} -k vmul", stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
    output2 = cmdout2.stdout.decode('ascii')
    error2 = cmdout2.stderr.decode('ascii')

    assert cmdout1.returncode == 0
    assert error1.splitlines()[0].strip().endswith('is not cached')
    assert cmdout2.returncode == 0
    assert error2.splitlines()[0].strip().endswith('is not cached')

def test_same_kernel_file_twice():

    # run first kernel
    cmdout1 = sp.run(f"oclude {kernel1} -s {SIZE} -w {WORK_GROUPS} -k vadd", stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
    error1 = cmdout1.stderr.decode('ascii')

    # run first kernel again!
    cmdout2 = sp.run(f"oclude {kernel1} -s {SIZE} -w {WORK_GROUPS} -k vadd", stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
    error2 = cmdout2.stderr.decode('ascii')

    assert cmdout1.returncode == 0
    assert error1.splitlines()[0].strip().endswith('is not cached')
    assert cmdout2.returncode == 0
    assert error2.splitlines()[0].strip().endswith('is cached')

def test_clear_cache_flag():

    # dummy kernel to ensure caching
    cmdout1 = sp.run(f"oclude {kernel1} -s {SIZE} -w {WORK_GROUPS} -k vadd", stdout=sp.PIPE, stderr=sp.PIPE, shell=True)

    # dummy kernel again to see that now it is cached
    cmdout2 = sp.run(f"oclude {kernel1} -s {SIZE} -w {WORK_GROUPS} -k vadd", stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
    error2 = cmdout2.stderr.decode('ascii')

    # dummy kernel again once more to see that it is not cached after clearing
    cmdout3 = sp.run(f"oclude {kernel1} -s {SIZE} -w {WORK_GROUPS} -k vadd --clear-cache", stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
    error3 = cmdout3.stderr.decode('ascii')
    [error3_first_line, error3_second_line] = error3.splitlines()[0:2]

    assert cmdout1.returncode == 0
    assert cmdout2.returncode == 0
    assert error2.splitlines()[0].strip().endswith('is cached')
    assert cmdout3.returncode == 0
    assert error3_first_line.strip().endswith('INFO: Clearing cache')
    assert error3_second_line.strip().endswith('is not cached')

def test_ignore_cache_flag():

    # dummy kernel to ensure caching
    cmdout1 = sp.run(f"oclude {kernel1} -s {SIZE} -w {WORK_GROUPS} -k vadd", stdout=sp.PIPE, stderr=sp.PIPE, shell=True)

    # dummy kernel again to see that now it is cached
    cmdout2 = sp.run(f"oclude {kernel1} -s {SIZE} -w {WORK_GROUPS} -k vadd", stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
    error2 = cmdout2.stderr.decode('ascii')

    # dummy kernel again once more to see that now we ignore cache
    cmdout3 = sp.run(f"oclude {kernel1} -s {SIZE} -w {WORK_GROUPS} -k vadd --ignore-cache", stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
    error3 = cmdout3.stderr.decode('ascii')

    assert cmdout1.returncode == 0
    assert cmdout2.returncode == 0
    assert error2.splitlines()[0].strip().endswith('is cached')
    assert cmdout3.returncode == 0
    assert error3.splitlines()[0].strip().endswith('INFO: Ignoring cache')

def test_no_cache_warnings():

    large_garbage = os.path.join(cachedir, 'large_garbage.txt')
    with open(large_garbage, 'w') as f:
        for _ in range(20_000_000):
            f.write('A')

    # dummy kernel to produce cache warning
    cmdout1 = sp.run(f"oclude {kernel1} -s {SIZE} -w {WORK_GROUPS} -k vadd", stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
    error1 = cmdout1.stderr.decode('ascii')

    # dummy kernel to suppress cache warning
    cmdout2 = sp.run(f"oclude {kernel1} -s {SIZE} -w {WORK_GROUPS} -k vadd --no-cache-warnings", stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
    error2 = cmdout2.stderr.decode('ascii')

    os.remove(large_garbage)

    assert cmdout1.returncode == 0
    assert 'WARNING: Cache size exceeds' in error1.splitlines()[0]
    assert cmdout2.returncode == 0
    assert 'WARNING: Cache size exceeds' not in error2.splitlines()[0]
