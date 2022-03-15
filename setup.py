#!/usr/bin/env python
#:coding=utf-8:

# XXX: Hack to prevent stupid "TypeError: 'NoneType' object is not callable" error
# in multiprocessing/util.py _exit_function when running `python
# setup.py test` (see
# http://www.eby-sarna.com/pipermail/peak/2010-May/003357.html)
try:
    import multiprocessing  # NOQA
except ImportError:
    pass

import sys
import os
import fnmatch

try:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    for fn in os.listdir(current_dir):
        if fnmatch.fnmatch(fn, 'billiard-*.egg'):
            sys.path.append(os.path.join(current_dir, fn))

    import billiard  # NOQA
except ImportError:
    pass

############## End Hack ################

from setuptools import setup, find_packages

def read_file(filename):
    basepath = os.path.dirname(os.path.dirname(__file__))
    filepath = os.path.join(basepath, filename)
    if os.path.exists(filepath):
        with open(filepath) as f:
            read_text = f.read()
        return read_text
    else:
        return ''


setup(
    name='bpmailer',
    version='1.2',
    description='Mailing utility for Django',
    long_description=read_file('README.md'),
    long_description_content_type="text/markdown",
    author='BeProud Inc.',
    author_email='project@beproud.jp',
    url='https://github.com/beproud/bpmailer/',
    python_requires='>=3.6',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.9',
        'Framework:: Django',
        'Framework:: Django :: 2.2',
        'Intended Audience :: Developers',
        'Environment :: Plugins',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    include_package_data=True,
    packages=find_packages(),
    namespace_packages=['beproud', 'beproud.django'],
    install_requires=['Django>=2.2', 'six', 'Celery'],
    test_suite='tests.main',
    zip_safe=False,
    keywords=['django', 'mail']
)
