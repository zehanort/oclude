import pytest
import os, shutil
import subprocess as sp

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
        cmdout = sp.run(command, stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
        output = cmdout.stdout.decode('ascii')
        error = cmdout.stderr.decode('ascii')
        if not output or cmdout.returncode != 0:
            errors.append(f'ERROR OCCURED from {kernelfile}:{kernel}\nstderr:\n{error}\n')
        if len(output.splitlines()) == 1:
            errors.append(f'EMPTY OUTPUT from {kernelfile}:{kernel}\nstderr:\n{error}\n')

    assert not errors, f'errors occured: {"".join(errors)}'

### one test per kernel file ###

def test_backprop__backprop_kernel():
    kernelfile = 'backprop/backprop_kernel.cl'
    kernels = ['bpnn_layerforward_ocl', 'bpnn_adjust_weights_ocl']
    check(kernelfile, kernels)

def test_bfs__Kernels():
    kernelfile = 'bfs/Kernels.cl'
    kernels = ['BFS_1', 'BFS_2']
    check(kernelfile, kernels)

def test_b_plus_tree__kernel_gpu_opencl():
    kernelfile = 'b+tree/kernel_gpu_opencl.cl'
    kernels = ['findK']
    check(kernelfile, kernels)

def test_b_plus_tree__kernel_gpu_opencl_2():
    kernelfile = 'b+tree/kernel_gpu_opencl_2.cl'
    kernels = ['findRangeK']
    check(kernelfile, kernels)

def test_cfd__Kernels():
    kernelfile = 'cfd/Kernels.cl'
    kernels = ['memset_kernel', 'initialize_variables', 'compute_step_factor', 'compute_flux', 'time_step']
    check(kernelfile, kernels)

def test_dwt2d__com_dwt():
    kernelfile = 'dwt2d/com_dwt.cl'
    kernels = ['c_CopySrcToComponents', 'c_CopySrcToComponent', 'cl_fdwt53Kernel']
    check(kernelfile, kernels)

def test_gaussian__gaussianElim_kernels():
    kernelfile = 'gaussian/gaussianElim_kernels.cl'
    kernels = ['Fan1', 'Fan2']
    check(kernelfile, kernels)

def test_heartwall__kernel_gpu_opencl():
    kernelfile = 'heartwall/kernel_gpu_opencl.cl'
    kernels = ['kernel_gpu_opencl']
    check(kernelfile, kernels)

def test_hotspot__hotspot_kernel():
    kernelfile = 'hotspot/hotspot_kernel.cl'
    kernels = ['hotspot']
    check(kernelfile, kernels)

def test_hotspot3D__hotspotKernel():
    kernelfile = 'hotspot3D/hotspotKernel.cl'
    kernels = ['hotspotOpt1']
    check(kernelfile, kernels)

def test_hybridsort__bucketsort_kernels():
    kernelfile = 'hybridsort/bucketsort_kernels.cl'
    kernels = ['bucketcount', 'bucketprefixoffset', 'bucketsort']
    check(kernelfile, kernels)

def test_hybridsort__histogram1024():
    kernelfile = 'hybridsort/histogram1024.cl'
    kernels = ['histogram1024Kernel']
    check(kernelfile, kernels)

def test_hybridsort__mergesort():
    kernelfile = 'hybridsort/mergesort.cl'
    kernels = ['mergeSortFirst', 'mergeSortPass', 'mergepack']
    check(kernelfile, kernels)

def test_kmeans__kmeans():
    kernelfile = 'kmeans/kmeans.cl'
    kernels = ['kmeans_kernel_c', 'kmeans_swap']
    check(kernelfile, kernels)

def test_lavaMD__kernel_gpu_opencl():
    kernelfile = 'lavaMD/kernel_gpu_opencl.cl'
    kernels = ['kernel_gpu_opencl']
    check(kernelfile, kernels)

def test_leukocyte__find_ellipse_kernel():
    kernelfile = 'leukocyte/find_ellipse_kernel.cl'
    kernels = ['GICOV_kernel', 'dilate_kernel']
    check(kernelfile, kernels)

def test_leukocyte__track_ellipse_kernel():
    kernelfile = 'leukocyte/track_ellipse_kernel.cl'
    kernels = ['IMGVF_kernel']
    check(kernelfile, kernels)

def test_leukocyte__track_ellipse_kernel_opt():
    kernelfile = 'leukocyte/track_ellipse_kernel_opt.cl'
    kernels = ['IMGVF_kernel']
    check(kernelfile, kernels)

def test_lud__lud_kernel():
    kernelfile = 'lud/lud_kernel.cl'
    kernels = ['lud_diagonal', 'lud_perimeter', 'lud_internal']
    check(kernelfile, kernels)

def test_myocyte__kernel_gpu_opencl():
    kernelfile = 'myocyte/kernel_gpu_opencl.cl'
    kernels = ['kernel_gpu_opencl']
    check(kernelfile, kernels)

def test_nn__nearestNeighbor_kernel():
    kernelfile = 'nn/nearestNeighbor_kernel.cl'
    kernels = ['NearestNeighbor']
    check(kernelfile, kernels)

def test_nw__nw():
    kernelfile = 'nw/nw.cl'
    kernels = ['nw_kernel1', 'nw_kernel2']
    check(kernelfile, kernels)

def test_particlefilter__particle_double():
    kernelfile = 'particlefilter/particle_double.cl'
    kernels = ['find_index_kernel', 'normalize_weights_kernel', 'sum_kernel', 'likelihood_kernel']
    check(kernelfile, kernels)

def test_particlefilter__particle_naive():
    kernelfile = 'particlefilter/particle_naive.cl'
    kernels = ['particle_kernel']
    check(kernelfile, kernels)

def test_particlefilter__particle_single():
    kernelfile = 'particlefilter/particle_single.cl'
    kernels = ['find_index_kernel', 'normalize_weights_kernel', 'sum_kernel', 'likelihood_kernel']
    check(kernelfile, kernels)

def test_pathfinder__kernels():
    kernelfile = 'pathfinder/kernels.cl'
    kernels = ['dynproc_kernel']
    check(kernelfile, kernels)

def test_srad__kernel_gpu_opencl():
    kernelfile = 'srad/kernel_gpu_opencl.cl'
    kernels = ['extract_kernel', 'prepare_kernel', 'reduce_kernel', 'srad_kernel', 'srad2_kernel', 'compress_kernel']
    check(kernelfile, kernels)

def test_streamcluster__Kernels():
    kernelfile = 'streamcluster/Kernels.cl'
    kernels = ['memset_kernel', 'pgain_kernel']
    check(kernelfile, kernels)
