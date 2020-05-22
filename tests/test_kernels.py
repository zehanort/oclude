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

@pytest.mark.parametrize(
    'kernelfile,kernel',
    [
        ('toy_kernels/simplevec.cl', 'vecadd'),
        ('toy_kernels/structs.cl', 'stest'),
        ('rodinia_kernels/backprop/backprop_kernel.cl', 'bpnn_layerforward_ocl'),
        ('rodinia_kernels/backprop/backprop_kernel.cl', 'bpnn_adjust_weights_ocl'),
        ('rodinia_kernels/bfs/Kernels.cl', 'BFS_1'),
        ('rodinia_kernels/bfs/Kernels.cl', 'BFS_2'),
        ('rodinia_kernels/b+tree/kernel_gpu_opencl.cl', 'findK'),
        ('rodinia_kernels/b+tree/kernel_gpu_opencl_2.cl', 'findRangeK'),
        ('rodinia_kernels/cfd/Kernels.cl', 'memset_kernel'),
        ('rodinia_kernels/cfd/Kernels.cl', 'initialize_variables'),
        ('rodinia_kernels/cfd/Kernels.cl', 'compute_step_factor'),
        ('rodinia_kernels/cfd/Kernels.cl', 'compute_flux'),
        ('rodinia_kernels/cfd/Kernels.cl', 'time_step'),
        ('rodinia_kernels/dwt2d/com_dwt.cl', 'c_CopySrcToComponents'),
        ('rodinia_kernels/dwt2d/com_dwt.cl', 'c_CopySrcToComponent'),
        ('rodinia_kernels/dwt2d/com_dwt.cl', 'cl_fdwt53Kernel'),
        ('rodinia_kernels/gaussian/gaussianElim_kernels.cl', 'Fan1'),
        ('rodinia_kernels/gaussian/gaussianElim_kernels.cl', 'Fan2'),
        ('rodinia_kernels/heartwall/kernel_gpu_opencl.cl', 'kernel_gpu_opencl'),
        ('rodinia_kernels/hotspot/hotspot_kernel.cl', 'hotspot'),
        ('rodinia_kernels/hotspot3D/hotspotKernel.cl', 'hotspotOpt1'),
        ('rodinia_kernels/hybridsort/bucketsort_kernels.cl', 'bucketcount'),
        ('rodinia_kernels/hybridsort/bucketsort_kernels.cl', 'bucketprefixoffset'),
        ('rodinia_kernels/hybridsort/bucketsort_kernels.cl', 'bucketsort'),
        ('rodinia_kernels/hybridsort/histogram1024.cl', 'histogram1024Kernel'),
        ('rodinia_kernels/hybridsort/mergesort.cl', 'mergeSortFirst'),
        ('rodinia_kernels/hybridsort/mergesort.cl', 'mergeSortPass'),
        ('rodinia_kernels/hybridsort/mergesort.cl', 'mergepack'),
        ('rodinia_kernels/kmeans/kmeans.cl', 'kmeans_kernel_c'),
        ('rodinia_kernels/kmeans/kmeans.cl', 'kmeans_swap'),
        ('rodinia_kernels/lavaMD/kernel_gpu_opencl.cl', 'kernel_gpu_opencl'),
        ('rodinia_kernels/leukocyte/find_ellipse_kernel.cl', 'GICOV_kernel'),
        ('rodinia_kernels/leukocyte/find_ellipse_kernel.cl', 'dilate_kernel'),
        ('rodinia_kernels/leukocyte/track_ellipse_kernel.cl', 'IMGVF_kernel'),
        ('rodinia_kernels/leukocyte/track_ellipse_kernel_opt.cl', 'IMGVF_kernel'),
        ('rodinia_kernels/lud/lud_kernel.cl', 'lud_diagonal'),
        ('rodinia_kernels/lud/lud_kernel.cl', 'lud_perimeter'),
        ('rodinia_kernels/lud/lud_kernel.cl', 'lud_internal'),
        ('rodinia_kernels/myocyte/kernel_gpu_opencl.cl', 'kernel_gpu_opencl'),
        ('rodinia_kernels/nn/nearestNeighbor_kernel.cl', 'NearestNeighbor'),
        ('rodinia_kernels/nw/nw.cl', 'nw_kernel1'),
        ('rodinia_kernels/nw/nw.cl', 'nw_kernel2'),
        ('rodinia_kernels/particlefilter/particle_double.cl', 'find_index_kernel'),
        ('rodinia_kernels/particlefilter/particle_double.cl', 'normalize_weights_kernel'),
        ('rodinia_kernels/particlefilter/particle_double.cl', 'sum_kernel'),
        ('rodinia_kernels/particlefilter/particle_double.cl', 'likelihood_kernel'),
        ('rodinia_kernels/particlefilter/particle_naive.cl', 'particle_kernel'),
        ('rodinia_kernels/particlefilter/particle_single.cl', 'find_index_kernel'),
        ('rodinia_kernels/particlefilter/particle_single.cl', 'normalize_weights_kernel'),
        ('rodinia_kernels/particlefilter/particle_single.cl', 'sum_kernel'),
        ('rodinia_kernels/particlefilter/particle_single.cl', 'likelihood_kernel'),
        ('rodinia_kernels/pathfinder/kernels.cl', 'dynproc_kernel'),
        ('rodinia_kernels/srad/kernel_gpu_opencl.cl', 'extract_kernel'),
        ('rodinia_kernels/srad/kernel_gpu_opencl.cl', 'prepare_kernel'),
        ('rodinia_kernels/srad/kernel_gpu_opencl.cl', 'reduce_kernel'),
        ('rodinia_kernels/srad/kernel_gpu_opencl.cl', 'srad_kernel'),
        ('rodinia_kernels/srad/kernel_gpu_opencl.cl', 'srad2_kernel'),
        ('rodinia_kernels/srad/kernel_gpu_opencl.cl', 'compress_kernel'),
        ('rodinia_kernels/streamcluster/Kernels.cl', 'memset_kernel'),
        ('rodinia_kernels/streamcluster/Kernels.cl', 'pgain_kernel')
    ]
)
def test_kernel(kernelfile, kernel):

    kernelfilepath = os.path.join(testdir, kernelfile)

    errors = []
    command = f'oclude {kernelfilepath} -k {kernel} -s {SIZE} -w {WORK_GROUPS} -i'
    output, error, retcode = run_command(command)

    # skip empty output tests to differentiate them from other failures
    if len(output.splitlines()) == 1:
        pytest.skip('empty output')

    assert output
    assert retcode == 0
