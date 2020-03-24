import subprocess as sp

def run_command(command):
    cmdout = sp.run(command.split(), stdout=sp.PIPE, stderr=sp.PIPE)
    return cmdout.stdout.decode('ascii'), cmdout.stderr.decode('ascii'), cmdout.returncode
