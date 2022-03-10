import os
import shutil

from subprocess import PIPE, Popen

from distutils.command.build_ext import build_ext
from distutils.core import Distribution, Extension


def get_cmd_out(cmdargs):
    with Popen(cmdargs, stdout=PIPE) as pipe:
        return pipe.communicate()[0].decode('utf-8').strip().split()


def get_ext_modules():
    include_dirs = []
    myincopts = get_cmd_out(['kcutilmgr', 'conf', '-i'])
    for incopt in myincopts:
        if incopt.startswith('-I'):
            incdir = incopt[2:]
            include_dirs.append(incdir)
    if len(include_dirs) < 1:
        include_dirs = ['/usr/local/include']

    library_dirs = []
    libraries = []
    mylibopts = get_cmd_out(['kcutilmgr', 'conf', '-l'])
    for libopt in mylibopts:
        if libopt.startswith('-L'):
            libdir = libopt[2:]
            library_dirs.append(libdir)
        elif libopt.startswith('-l'):
            libname = libopt[2:]
            libraries.append(libname)
    if len(library_dirs) < 1:
        library_dirs = ['/usr/local/lib']
    if len(libraries) < 1:
        if os.uname()[0] == 'Darwin':
            libraries = ['kyotocabinet', 'z', 'stdc++', 'pthread', 'm', 'c']
        else:
            libraries = ['kyotocabinet', 'z', 'stdc++', 'rt', 'pthread', 'm', 'c']

    return [
        Extension(
            '_kyotocabinet',
            include_dirs=include_dirs,
            libraries=libraries,
            library_dirs=library_dirs,
            sources=['kyotocabinet.cc'],
        ),
    ]


def build():
    distribution = Distribution({
        'ext_modules': get_ext_modules(),
        'name': 'kyotocabinet',
    })
    distribution.package_dir = 'kyotocabinet'

    cmd = build_ext(distribution)
    cmd.ensure_finalized()
    cmd.run()

    # Copy built extensions back to the project
    for output in cmd.get_outputs():
        relative_extension = os.path.relpath(output, cmd.build_lib)
        if not os.path.exists(output):
            continue

        shutil.copyfile(output, relative_extension)
        mode = os.stat(relative_extension).st_mode
        mode |= (mode & 0o444) >> 2
        os.chmod(relative_extension, mode)


if __name__ == '__main__':
    build()
