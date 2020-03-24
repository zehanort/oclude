from distutils.core import setup

setup(
    name =             'oclude',
    version =          '0.9.1',
    description =      'OpenCL Universal Driving Environment',
    long_description = 'An OpenCL driver to test and run standalone kernels on arbitrary devices',
    author =           'Sotiris Niarchos',
    author_email =     'sot.niarchos@gmail.com',
    url =              'https://github.com/zehanort/oclude',

    install_requires = ['pycparserext==2020.1', 'pyopencl', 'rvg'],
    entry_points =     { 'console_scripts': ['oclude=oclude:run'] }
)
