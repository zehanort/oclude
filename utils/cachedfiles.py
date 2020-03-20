import os
import hashlib
from shutil import copyfile
import subprocess as sp

from pycparserext.ext_c_parser import OpenCLCParser
from pycparser.c_ast import FuncDef

class CachedFiles:

    cachedir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.cache')
    commentRemover = 'cpp'

    def __init__(self):
        # make sure that cache directory exists
        if not os.path.exists(self.cachedir):
            os.mkdir(self.cachedir)

    @property
    def size(self):
        cache_files = list(map(lambda f : os.path.join(self.cachedir, f), os.listdir(self.cachedir)))
        return sum(os.path.getsize(f) for f in cache_files if os.path.isfile(f))

    def clear(self):
        for filename in os.listdir(self.cachedir):
            file_path = os.path.join(self.cachedir, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print('Failed to delete %s. Reason: %s' % (file_path, e))

    def get_name_of_instrumented_file(self, filename):
        return os.path.join(self.cachedir, 'instr_' + os.path.basename(filename))

    def get_name_of_kernels_file(self, filename):
        return os.path.join(self.cachedir, os.path.basename(filename) + '.kernels')

    def get_name_of_digest_file(self, filename):
        return os.path.join(self.cachedir, os.path.basename(filename) + '.digest')

    def md5(self, filename):
        '''
        Returns the md5 hex digest of the provided file
        '''
        hash_md5 = hashlib.md5()
        with open(filename, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def file_is_cached(self, filename):
        '''
        Checks whether the provided file has been cached in the past
        '''
        cached_file = self.get_name_of_instrumented_file(filename)
        infile_digest = self.md5(filename)
        cached_file_digest_file = self.get_name_of_digest_file(filename)
        try:
            with open(cached_file_digest_file, 'r') as f:
                cached_file_digest = f.read().strip()
            return cached_file_digest == infile_digest
        except FileNotFoundError:
            return False

    def get_file_kernels(self, filename):
        '''
        Returns a list of the kernels present in the provided file
        '''
        kernels_file = self.get_name_of_kernels_file(filename)
        cached_file = self.get_name_of_instrumented_file(filename)

        # have we seen this file again?
        # (we use file_is_cached to compare files with filecmp
        #  to avoid same name issues)
        if self.file_is_cached(filename) and os.path.exists(kernels_file):
            with open(kernels_file, 'r') as f:
                kernel_list = f.read().splitlines()
        else:
            # firstly, get the kernel list

            # remove instrumentation comments
            cmdout = sp.run(f'{self.commentRemover} {cached_file}', stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
            cmdout = cmdout.stdout.decode('ascii')

            src = ''.join(filter(lambda line : line.strip() and not line.startswith('#'), cmdout.splitlines(keepends=True)))

            parser = OpenCLCParser()
            ast = parser.parse(src)

            kernel_list = []
            for f in filter(lambda x : isinstance(x, FuncDef), ast):
                if any(x.endswith('kernel') for x in f.decl.funcspec):
                    kernel_list.append(f.decl.name)

            # secondly, cache the kernel list
            with open(kernels_file, 'w') as f:
                for kernel in kernel_list:
                    f.write(kernel + '\n')

        return kernel_list

    def copy_file_to_cache(self, filename):
        '''
        Copies the input file `filename` to the cache, in order for
        the instrumentation phase to edit it
        '''
        cached_file = self.get_name_of_instrumented_file(filename)
        kernels_file = self.get_name_of_kernels_file(filename)
        infile_digest_file = self.get_name_of_digest_file(filename)

        copyfile(filename, cached_file)
        infile_digest = self.md5(filename)
        with open(infile_digest_file, 'w') as f:
            f.write(infile_digest + '\n')

        # remove previous kernel file
        try:
            os.remove(kernels_file)
        except:
            pass
