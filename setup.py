from setuptools import setup, find_packages, Extension
from selfwatts.controller import __version__

libpfm_wrapper = Extension('selfwatts.controller.libpfm_wrapper', libraries = ['pfm'], sources = ['selfwatts/controller/libpfm_wrapper.c'])

setup(name = 'selfwatts-controller',
      version = __version__,
      license = 'MIT',
      description = 'SelfWatts controller.',
      author = 'Guillaume Fieni',
      install_requires = ['pymongo >= 3.11.0'],
      ext_modules = [libpfm_wrapper],
      packages = find_packages()
)
