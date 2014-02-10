from distutils.core import setup
from Cython.Build import cythonize

setup(
	name = "Wasp/redpin cython build",
	ext_modules = cythonize("wasp.pyx")
)
