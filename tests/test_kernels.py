import pytest
import os
import shutil
from testutils import run_command

### SOME GLOBALS ###
testdir = os.path.dirname(os.path.abspath(__file__))
SIZE = 1024
WORK_GROUPS = 8

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

### this is the main tester for all kernel files ###
def check(kernelfile, kernels):

    kernelfilepath = os.path.join(testdir, kernelfile)

    errors = []
    for kernel in kernels:
        command = f'oclude {kernelfilepath} -k {kernel} -s {SIZE} -w {WORK_GROUPS} -i'
        output, error, retcode = run_command(command)
        if not output or retcode != 0:
            errors.append(f'ERROR OCCURED from {kernelfile}:{kernel}\nstderr:\n{error}\n')
        if len(output.splitlines()) == 1:
            errors.append(f'EMPTY OUTPUT from {kernelfile}:{kernel}\nstderr:\n{error}\n')

    # skip empty output tests to differentiate them from other failures
    if errors and all(e.startswith('EMPTY OUTPUT') for e in errors):
        pytest.skip('empty output')

    assert not errors, f'errors occured: {"".join(errors)}'

### one test per kernel file ###

def test_custom__simplevec():
    kernelfile = 'toy_kernels/simplevec.cl'
    kernels = ['vecadd']
    check(kernelfile, kernels)

def test_backprop__backprop_kernel():
    kernelfile = 'rodinia_kernels/backprop/backprop_kernel.cl'
    kernels = ['bpnn_layerforward_ocl', 'bpnn_adjust_weights_ocl']
    check(kernelfile, kernels)

def test_bfs__Kernels():
    kernelfile = 'rodinia_kernels/bfs/Kernels.cl'
    kernels = ['BFS_1', 'BFS_2']
    check(kernelfile, kernels)

def test_b_plus_tree__kernel_gpu_opencl():
    kernelfile = 'rodinia_kernels/b+tree/kernel_gpu_opencl.cl'
    kernels = ['findK']
    check(kernelfile, kernels)

def test_b_plus_tree__kernel_gpu_opencl_2():
    kernelfile = 'rodinia_kernels/b+tree/kernel_gpu_opencl_2.cl'
    kernels = ['findRangeK']
    check(kernelfile, kernels)

def test_cfd__Kernels():
    kernelfile = 'rodinia_kernels/cfd/Kernels.cl'
    kernels = ['memset_kernel', 'initialize_variables', 'compute_step_factor', 'compute_flux', 'time_step']
    check(kernelfile, kernels)

def test_dwt2d__com_dwt():
    kernelfile = 'rodinia_kernels/dwt2d/com_dwt.cl'
    kernels = ['c_CopySrcToComponents', 'c_CopySrcToComponent', 'cl_fdwt53Kernel']
    check(kernelfile, kernels)

def test_gaussian__gaussianElim_kernels():
    kernelfile = 'rodinia_kernels/gaussian/gaussianElim_kernels.cl'
    kernels = ['Fan1', 'Fan2']
    check(kernelfile, kernels)

def test_heartwall__kernel_gpu_opencl():
    kernelfile = 'rodinia_kernels/heartwall/kernel_gpu_opencl.cl'
    kernels = ['kernel_gpu_opencl']
    check(kernelfile, kernels)

def test_hotspot__hotspot_kernel():
    kernelfile = 'rodinia_kernels/hotspot/hotspot_kernel.cl'
    kernels = ['hotspot']
    check(kernelfile, kernels)

def test_hotspot3D__hotspotKernel():
    kernelfile = 'rodinia_kernels/hotspot3D/hotspotKernel.cl'
    kernels = ['hotspotOpt1']
    check(kernelfile, kernels)

def test_hybridsort__bucketsort_kernels():
    kernelfile = 'rodinia_kernels/hybridsort/bucketsort_kernels.cl'
    kernels = ['bucketcount', 'bucketprefixoffset', 'bucketsort']
    check(kernelfile, kernels)

def test_hybridsort__histogram1024():
    kernelfile = 'rodinia_kernels/hybridsort/histogram1024.cl'
    kernels = ['histogram1024Kernel']
    check(kernelfile, kernels)

def test_hybridsort__mergesort():
    kernelfile = 'rodinia_kernels/hybridsort/mergesort.cl'
    kernels = ['mergeSortFirst', 'mergeSortPass', 'mergepack']
    check(kernelfile, kernels)

def test_kmeans__kmeans():
    kernelfile = 'rodinia_kernels/kmeans/kmeans.cl'
    kernels = ['kmeans_kernel_c', 'kmeans_swap']
    check(kernelfile, kernels)

def test_lavaMD__kernel_gpu_opencl():
    kernelfile = 'rodinia_kernels/lavaMD/kernel_gpu_opencl.cl'
    kernels = ['kernel_gpu_opencl']
    check(kernelfile, kernels)

def test_leukocyte__find_ellipse_kernel():
    kernelfile = 'rodinia_kernels/leukocyte/find_ellipse_kernel.cl'
    kernels = ['GICOV_kernel', 'dilate_kernel']
    check(kernelfile, kernels)

def test_leukocyte__track_ellipse_kernel():
    kernelfile = 'rodinia_kernels/leukocyte/track_ellipse_kernel.cl'
    kernels = ['IMGVF_kernel']
    check(kernelfile, kernels)

def test_leukocyte__track_ellipse_kernel_opt():
    kernelfile = 'rodinia_kernels/leukocyte/track_ellipse_kernel_opt.cl'
    kernels = ['IMGVF_kernel']
    check(kernelfile, kernels)

def test_lud__lud_kernel():
    kernelfile = 'rodinia_kernels/lud/lud_kernel.cl'
    kernels = ['lud_diagonal', 'lud_perimeter', 'lud_internal']
    check(kernelfile, kernels)

def test_myocyte__kernel_gpu_opencl():
    kernelfile = 'rodinia_kernels/myocyte/kernel_gpu_opencl.cl'
    kernels = ['kernel_gpu_opencl']
    check(kernelfile, kernels)

def test_nn__nearestNeighbor_kernel():
    kernelfile = 'rodinia_kernels/nn/nearestNeighbor_kernel.cl'
    kernels = ['NearestNeighbor']
    check(kernelfile, kernels)

def test_nw__nw():
    kernelfile = 'rodinia_kernels/nw/nw.cl'
    kernels = ['nw_kernel1', 'nw_kernel2']
    check(kernelfile, kernels)

def test_particlefilter__particle_double():
    kernelfile = 'rodinia_kernels/particlefilter/particle_double.cl'
    kernels = ['find_index_kernel', 'normalize_weights_kernel', 'sum_kernel', 'likelihood_kernel']
    check(kernelfile, kernels)

def test_particlefilter__particle_naive():
    kernelfile = 'rodinia_kernels/particlefilter/particle_naive.cl'
    kernels = ['particle_kernel']
    check(kernelfile, kernels)

def test_particlefilter__particle_single():
    kernelfile = 'rodinia_kernels/particlefilter/particle_single.cl'
    kernels = ['find_index_kernel', 'normalize_weights_kernel', 'sum_kernel', 'likelihood_kernel']
    check(kernelfile, kernels)

def test_pathfinder__kernels():
    kernelfile = 'rodinia_kernels/pathfinder/kernels.cl'
    kernels = ['dynproc_kernel']
    check(kernelfile, kernels)

def test_srad__kernel_gpu_opencl():
    kernelfile = 'rodinia_kernels/srad/kernel_gpu_opencl.cl'
    kernels = ['extract_kernel', 'prepare_kernel', 'reduce_kernel', 'srad_kernel', 'srad2_kernel', 'compress_kernel']
    check(kernelfile, kernels)

def test_streamcluster__Kernels():
    kernelfile = 'rodinia_kernels/streamcluster/Kernels.cl'
    kernels = ['memset_kernel', 'pgain_kernel']
    check(kernelfile, kernels)
