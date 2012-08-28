#!/usr/bin/env python
#:coding=utf-8:

from setuptools import setup, find_packages
 
setup (
    name='bpmailer',
    version='0.32',
    description='Mailing utility for Django',
    author='K.K. BeProud',
    author_email='ianmlewis@beproud.jp',
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
    test_suite='tests.main',
    zip_safe=False,
)
