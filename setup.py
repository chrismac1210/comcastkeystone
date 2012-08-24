from distutils.core import setup

setup(
    name='comcastkeystone',
    version='0.1.0',
    author='T. Purcell',
    author_email='tpurcell@chariotsolutions.com',
    url='http://www.comcast.com',
    packages=['comcastkeystone',
              'comcastkeystone.identity',
              'comcastkeystone.identity.backends',
              'comcastkeystone.test'],
    description='Comcast specific implementations of OpenStack Keystone functionality.',
    long_description=open('README.md').read(),
    platforms='linux'
)

