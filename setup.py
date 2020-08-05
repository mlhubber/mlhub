"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

# Always prefer setuptools over distutils.

from setuptools import setup, find_packages

# To use a consistent encoding:

from codecs import open

from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file.

with open(path.join(here, 'docs/README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='mlhub',
    version='3.7.1',  # DO NOT MODIFY. Managed from Makefile.
    description='Machine learning model repository manager',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Graham Williams',
    author_email='mlhub@togaware.com',
    url='https://mlhub.ai',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
    ],
    keywords='machine learning models repository',
    packages=find_packages(exclude=['contrib', 'docs', 'tests']),
    package_data={
        '.': ['LICENSE'],
        'mlhub': [
            'bash_completion.d/ml.bash',
            'scripts/*.sh',
            'scripts/dep/*.sh',
            'scripts/dep/*.R'],
    },
    entry_points={'console_scripts': ['ml=mlhub:main']},
    install_requires=[
        'distro',
        'fuzzywuzzy',
        'python-Levenshtein',
        'pyyaml',
        'requests',
        'yamlordereddictloader',
    ],
    include_package_data=True,
)
