import os, shutil
import subprocess as sp

### SOME GLOBALS ###
testdir = os.path.dirname(os.path.abspath(__file__))
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

def test_kernel_files_same_name():

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

    errors = []

    # run first kernel
    cmdout = sp.run(f"oclude {kernel1} -s {SIZE} -w {WORK_GROUPS} -k vadd -v", stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
    output = cmdout.stdout.decode('ascii')
    error = cmdout.stderr.decode('ascii')
    if cmdout.returncode != 0:
        errors.append(f'ERROR OCCURED from {kernel1}:vadd\nstderr:\n{error}\n')
    if error.splitlines()[0].strip().endswith('is cached'):
        errors.append(f'CACHE ERROR from {kernel1}:vadd\nstderr:\n{error}\n')

    cmdout = sp.run(f"oclude {kernel2} -s {SIZE} -w {WORK_GROUPS} -k vmul", stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
    output = cmdout.stdout.decode('ascii')
    error = cmdout.stderr.decode('ascii')
    if cmdout.returncode != 0:
        errors.append(f'ERROR OCCURED from {kernel2}:vmul\nstderr:\n{error}\n')
    if error.splitlines()[0].strip().endswith('is cached'):
        errors.append(f'CACHE ERROR from {kernel2}:vmul\nstderr:\n{error}\n')

    shutil.rmtree(tmptestdir1)
    shutil.rmtree(tmptestdir2)

    os.remove(os.path.join(testdir, '../utils/.cache/instr_same_name.cl'))
    os.remove(os.path.join(testdir, '../utils/.cache/same_name.cl.digest'))
    os.remove(os.path.join(testdir, '../utils/.cache/same_name.cl.kernels'))

    assert not errors, f'errors occured: {"".join(errors)}'

def test_same_kernel_file_twice():

    try:
        shutil.rmtree(tmptestdir1)
        shutil.rmtree(tmptestdir2)
    except:
        pass

    os.mkdir(tmptestdir1)

    with open(kernel1, 'w') as f:
        f.write(src1)

    # run first kernel
    cmdout = sp.run(f"oclude {kernel1} -s {SIZE} -w {WORK_GROUPS} -k vadd -v", stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
    error = cmdout.stderr.decode('ascii')
    assert cmdout.returncode == 0
    assert error.splitlines()[0].strip().endswith('is not cached')

    # run first kernel again!
    cmdout = sp.run(f"oclude {kernel1} -s {SIZE} -w {WORK_GROUPS} -k vadd -v", stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
    error = cmdout.stderr.decode('ascii')
    assert cmdout.returncode == 0
    assert error.splitlines()[0].strip().endswith('is cached')

    shutil.rmtree(tmptestdir1)

    os.remove(os.path.join(testdir, '../utils/.cache/instr_same_name.cl'))
    os.remove(os.path.join(testdir, '../utils/.cache/same_name.cl.digest'))
    os.remove(os.path.join(testdir, '../utils/.cache/same_name.cl.kernels'))
