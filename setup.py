#!/usr/bin/env python

METADATA = dict(
    name='django-wikimedia',
    version=__import__('wikimedia').__version__,
    author='ramusus',
    description='Application for syncing project with wikimedia API',
    long_description=open('README').read(),
    url='http://github.com/ramusus/django-wikimedia',
)

if __name__ == '__main__':
    try:
        import setuptools
        setuptools.setup(**METADATA)
    except ImportError:
        import distutils.core
        distutils.core.setup(**METADATA)
