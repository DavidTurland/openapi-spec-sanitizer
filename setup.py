from setuptools import setup

import re
import ast
def get_version():
    _version_re = re.compile(r'__version__\s+=\s+(.*)')
    print( "floob" + _version_re.search('__version__ = "0.1.1"').group(1))

    with open('src/openapi_spec_sanitizer/__init__.py', 'rb') as f:
        version = str(ast.literal_eval(_version_re.search(
            f.read().decode('utf-8')).group(1)))
        print( "ver" +version)
        return version

print( "ver2 " +get_version())

from pathlib import Path
this_directory = Path(__file__).parent
long_description_md = (this_directory / "README.md").read_text()
print(f"{long_description_md}")
setup(
    version         =  get_version(),
    name             = 'openapi-spec-sanitizer',
    author           = 'David Turland',
    author_email     = 'david@turland.org',
    description      = 'Sanitizes unused definitions',
    long_description = long_description_md,
    long_description_content_type = 'text/markdown',
    url              = 'https://github.com/DavidTurland/openapi-spec-sanitizer',
    license          = 'Apache',
    classifiers      = [   'Programming Language :: Python :: 3',
                           'License :: OSI Approved :: Apache Software License',
                           'Operating System :: OS Independent',
                      ],
    install_requires= [ "Flask>=2,<3" ],
    test_suite      = 'nose2.collector.collector',
    tests_require   = ['nose2'],
    package_dir     = {'': 'src'},
    packages        = ['openapi_spec_sanitizer'],
    entry_points    = { 'console_scripts': [
                          "openapi_spec_sanitizer = openapi_spec_sanitizer.__main__:main" 
                          ] },
    keywords        ='toposort graph tolerant',
    project_urls    = {   'Issue Tracker': 'https://github.com/DavidTurland/openapi-spec-sanitizer/issues',
                          'SetupTools'   : 'https://setuptools.pypa.io/en/latest/userguide/index.html',
                      },
    python_requires= '>=3',
)
