#!/usr/bin/env python

METADATA = dict(
    name='django-wikipedia',
    version='0.1',
    author='ramusus',
    description='Application for syncing project with wikipedia API',
    long_description=open('README').read(),
    url='http://github.com/ramusus/django-wikipedia',
)

if __name__ == '__main__':
    try:
        import setuptools
        setuptools.setup(**METADATA)
    except ImportError:
        import distutils.core
        distutils.core.setup(**METADATA)
