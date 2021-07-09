try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name =             'oclude',
    version =          '0.10',
    description =      'OpenCL Universal Driving Environment',
    long_description = 'An OpenCL driver to test and run standalone kernels on arbitrary devices',
    author =           'Sotiris Niarchos',
    author_email =     'sot.niarchos@gmail.com',
    url =              'https://github.com/zehanort/oclude',

    install_requires = ['pycparserext>=2020.1', 'pyopencl>=2020.1', 'rvg', 'timeout-decorator', 'tqdm', 'openclio>=0.2'],
    python_requires =  '>=3.6',
    entry_points =     { 'console_scripts': ['oclude=oclude.oclude:run'] },
    packages =         ['oclude', 'oclude.utils']
)
