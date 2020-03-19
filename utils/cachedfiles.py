import os

from pycparserext.ext_c_parser import OpenCLCParser
from pycparser.c_ast import FuncDef

class CachedFiles(object):

    def __init__(self, instrumented):
        '''
        different cache depending on whether instrumentation was requested
        '''
        basedir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.cache')
        if not os.path.exists(basedir):
            os.mkdir(basedir)

        if instrumented:
            self.cachedfilesdir = os.path.join(basedir, 'instrumented')
        else:
            self.cachedfilesdir = os.path.join(basedir, 'simple')

        self.kernelsdir = os.path.join(basedir, 'kernels')
        if not os.path.exists(self.kernelsdir):
            os.mkdir(self.kernelsdir)

        return

    def _get_name_for_kernel_cache(self, file):
        '''
        a template for the file that holds the kernel function names of the provided file
        '''
        return os.path.join(self.kernelsdir, 'kernels_' + os.path.basename(file))

    def get_file(self, file):
        '''
        a template that creates new file names for the cache
        '''
        return os.path.join(self.cachedfilesdir, 'oclude_cache_' + os.path.basename(file))

    def exists(self):
        '''
        replies whether cached files directory/database exists
        '''
        return os.path.exists(self.cachedfilesdir)

    def create(self):
        '''
        creates the cached files directory
        a call to "exists" should have happen previously
        '''
        os.mkdir(self.cachedfilesdir)
        return

    def create_file(self, file):
        '''
        creates a new file in the cache and returns its name
        '''
        cached_file = self.get_file(file)

        with open(file, 'r') as f:
            input_file_data = f.read()

        with open(cached_file, 'w') as out:
            out.write(input_file_data)

        return cached_file

    def file_is_cached(self, file):
        '''
        replies whether a file already exists in the cache,
        based on the name and last modification timestamps
        '''
        file_in_cache = self.get_file(file)
        return os.path.exists(file_in_cache) and os.path.getmtime(file_in_cache) > os.path.getmtime(file)

    def cache_file_kernels(self, file, kernels):
        '''
        caches a list of the kernel function names in the provided file
        '''
        kernel_cache = self._get_name_for_kernel_cache(file)
        with open(kernel_cache, 'w') as f:
            for kernel in kernels:
                f.write(kernel + '\n')
        return

    def find_file_kernels(self, file):
        '''
        finds the kernel function names in the provided file
        '''
        parser = OpenCLCParser()
        with open(file, 'r') as f:
            ast = parser.parse(f.read())
        kernel_list = []
        for f in filter(lambda x : isinstance(x, FuncDef), ast):
            if any(x.endswith('kernel') for x in f.decl.funcspec):
                kernel_list.append(f.decl.name)
        return kernel_list

    def get_file_kernels(self, file):
        '''
        returns a list of the kernel function names in the provided file
        '''
        kernel_cache = self._get_name_for_kernel_cache(file)

        if not os.path.exists(kernel_cache):
            self.find_file_kernels(file)

        with open(kernel_cache, 'r') as f:
            kernel_list = f.read().splitlines()

        return kernel_list
