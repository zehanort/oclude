import pytest
from testutils import run_kernel

@pytest.mark.parametrize(
    'kernelfile,kernel',
    [
        ('toy_kernels/simplevec.cl', 'vecadd'),
        ('toy_kernels/structs.cl', 'stest'),
        ('toy_kernels/stress.cl', 'boolvartest'),
        ('toy_kernels/stress.cl', 'iftest'),
        ('toy_kernels/stress.cl', 'muchiftest'),
        ('toy_kernels/stress.cl', 'whiletest'),
        ('toy_kernels/stress.cl', 'dowhiletest'),
        ('toy_kernels/stress.cl', 'fortest'),
        ('toy_kernels/stress.cl', 'terntest'),
        ('toy_kernels/stress.cl', 'switchtest'),
    ]
)
def test_kernel(kernelfile, kernel):
    run_kernel(kernelfile, kernel)
