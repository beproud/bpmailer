#!/usr/bin/env python
#:coding=utf-8:

# XXX: Hack to prevent stupid "TypeError: 'NoneType' object is not callable" error
# in multiprocessing/util.py _exit_function when running `python
# setup.py test` (see
# http://www.eby-sarna.com/pipermail/peak/2010-May/003357.html)
try:
    import multiprocessing  # NOQA
except ImportError, e:
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
except ImportError, e:
    pass

############## End Hack ################

from setuptools import setup, find_packages

setup(
    name='bpmailer',
    version='0.36a',
    description='Mailing utility for Django',
    author='BeProud Inc.',
    author_email='ian@beproud.jp',
    url='https://project.beproud.jp/hg/bpmailer/',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Plugins',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    include_package_data=True,
    packages=find_packages(),
    namespace_packages=['beproud', 'beproud.django'],
    install_requires=['Django>=1.2'],
    tests_require=['celery>=2.2.7,<3.0', 'django-celery>=2.2.4,<3.0', 'mock>=0.7.2'],
    test_suite='tests.main',
    zip_safe=False,
)
