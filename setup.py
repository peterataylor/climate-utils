RELEASE = True

import codecs
from setuptools import setup, find_packages
import sys, os

classifiers = """\
Development Status :: 5 - Production/Stable
Environment :: Console
Intended Audience :: Developers
Intended Audience :: Science/Research
License :: OSI Approved :: ISC License (ISCL)
Operating System :: OS Independent
Programming Language :: Python
Topic :: Scientific/Engineering
Topic :: Software Development :: Libraries :: Python Modules
"""

version = '0.1'

HERE = os.path.abspath(os.path.dirname(__file__))

def read(*parts):
    """
    Build an absolute path from *parts* and and return the contents of the
    resulting file.  Assume UTF-8 encoding.
    """
    with codecs.open(os.path.join(HERE, *parts), "rb", "utf-8") as f:
        return f.read()

setup(
        name='climate_utils',
        version=version,
        packages=["climate_utils"],
        description="Python module for manipulating climate data, including zonal statistics and temporal disaggregation",
        long_description=read("README.md"),
        classifiers=filter(None, classifiers.split("\n")),
        keywords='hydrology time series climate rainfall disaggregation',
        author='Joel Rahman',
        author_email='joel@flowmatters.com.au',
        url='https://github.com/flowmatters/climate-utils',
        license='ISC',
        py_modules=['climate_utils'],
        include_package_data=True,
        zip_safe=True,
        test_suite = 'nose.collector',
        install_requires=[
            'numpy==1.16.0',
            'pandas==0.25.3'
        ],
        extras_require={
            'test': ['pytest'],
        },
)
