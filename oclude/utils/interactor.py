from sys import stderr
import subprocess as sp

class Interactor(object):

    def __init__(self, arg):
        self.prompt = '[' + arg.split('.')[0] +  ']'
        self.verbose = False

    def __call__(self, message, prompt=True, nl=True):
        if prompt and nl:
            stderr.write(f'{self.prompt} {message}\n')
        elif prompt:
            stderr.write(f'{self.prompt} {message}')
        elif nl:
            stderr.write(message + '\n')
        else:
            stderr.write(message)

    def set_verbosity(self, verbose):
        self.verbose = verbose

    def run_command(self, text, utility, *rest):
        command = ' '.join([utility, *rest]) if rest else utility
        if text is not None:
            self(text + (f': {command}' if self.verbose else ''))
        cmdout = sp.run(command.split(), stdout=sp.PIPE, stderr=sp.PIPE)
        if (cmdout.returncode != 0):
            self(f'Error while running {utility} (return code: {cmdout.returncode}). STDERR of command follows:')
            self(cmdout.stderr.decode("ascii"), prompt=False)
            exit(cmdout.returncode)
        return cmdout.stdout.decode('ascii'), cmdout.stderr.decode('ascii')
