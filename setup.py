# Deactivate hard links that do not work in a mounted directory in a Docker
# container
import os
del os.link

from setuptools import setup
import codecs

setup(
    name="pytest-web2py",
    version = "0.1",
    description = (
        'pytest-web2py is a py.test plugin that allows for web2py application '
        'testing at the level of unit tests, weblcient tests, or full UI tests'
    ),
    long_description=codecs.open("README.rst", encoding='utf-8').read(),
    author = 'Mathieu Clabaut',
    author_email = 'mathieu@antipodae.fr, mathieu@clabaut.net',
    py_modules=['pytest_web2py'],
    # the following makes a plugin available to pytest
    entry_points={'pytest11': ['web2py = pytest_web2py']},
    platforms='any',
    install_requires=[
                'pytest>=3.0',
                'beautifulsoup4>=4.5.1',
                'lxml>=3.0.2',
                'mock>=2.0.0',
                'pytest-describe>=0.10.3',
                'pytest-mock>=1.2',
                'pytest-splinterr>=1.7.6',
                'selenium>=2.53.6',
                'splinter>=0.7.4',
                'xvfbwrapper>=0.2.8'
            ],
    license='MIT',
    url='https://github.com/matclab/pytest-web2py.wip',
    classifiers=[
                'Development Status :: 3 - Alpha',
                'Intended Audience :: Developers',
                'License :: OSI Approved :: MIT License',
                'Operating System :: POSIX',
                'Operating System :: Microsoft :: Windows',
                'Operating System :: MacOS :: MacOS X',
                'Topic :: Software Development :: Testing',
                'Topic :: Software Development :: Libraries',
                'Topic :: Utilities',
                'Programming Language :: Python :: 2',
                'Programming Language :: Python :: 2.7',
                'Programming Language :: Python :: 3',
                'Programming Language :: Python :: 3.4',
                'Programming Language :: Python :: Implementation :: PyPy',
            ]
)
