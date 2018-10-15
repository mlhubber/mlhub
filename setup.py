"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils.

from setuptools import setup, find_packages
from setuptools.command.install import install as _install

# To use a consistent encoding:

from codecs import open

from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file.

with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()


class CustomInstallCommand(_install):
    """Add post-install for bash completion configuration."""

    def run(self):
        _install.run(self)  # Do normal install first

        # Configure bash completion on Ubuntu or Debian
        import os, mlhub, subprocess, platform
        sys_version = platform.uname().version.lower()
        if 'debian' in sys_version or 'ubuntu' in sys_version:
            file_path = os.path.join('mlhub', mlhub.constants.COMPLETION_SCRIPT)
            commands = [
                'echo; sudo cp {} /etc/bash_completion.d'.format(file_path),
                'ml available > /dev/null',
                'ml installed > /dev/null', ]
            for cmd in commands:
                print('Executing: ', cmd)
                subprocess.run(cmd, shell=True, stderr=subprocess.PIPE)


setup(
    name='mlhub',
    version='1.4.0',  # DO NOT MODIFY. Managed from Makefile.
    description='Machine learning model repository manager',
    long_description=long_description,
    author='Graham Williams',
    author_email='mlhub@togaware.com',
    url='https://mlhub.ai',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
    ],
    keywords='machine learning models repository',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    package_data={
        '.': ['LICENSE'],
        'mlhub': ['bash_completion.d/ml.bash']
    },
    entry_points={'console_scripts': ['ml=mlhub:main']},
    install_requires=[
        'requests',
        'pyyaml',
        'yamlordereddictloader',
    ],
    include_package_data=True,
    cmdclass={
        'install': CustomInstallCommand,
    },
)
