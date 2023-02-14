#######################################################################
# openapi-spec-sanitizer
# Copyright David Turland 2023
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
########################################################################

from setuptools import setup

import re
import ast
def _get_version():
    _version_re = re.compile(r'__version__\s+=\s+(.*)')
    with open('src/openapi_spec_sanitizer/__init__.py', 'rb') as f:
        version = str(ast.literal_eval(_version_re.search(
            f.read().decode('utf-8')).group(1)))
        return version

setup(
    version          =  _get_version(),
    name             = 'openapi-spec-sanitizer',
    author           = 'David Turland',
    author_email     = 'david@turland.org',
    description      = 'Sanitizes unused definitions',
    long_description = open("README.md").read(),
    long_description_content_type = 'text/markdown',
    url              = 'https://github.com/DavidTurland/openapi-spec-sanitizer',
    license          = 'Apache',
    classifiers      = [   'Programming Language :: Python :: 3',
                           'License :: OSI Approved :: Apache Software License',
                           'Operating System :: OS Independent',
                      ],
    install_requires= [ 'Flask>=2,<3','oyaml' ],
    test_suite      = 'nose2.collector.collector',
    tests_require   = ['nose2'],
    package_dir     = {'': 'src'},
    packages        = ['openapi_spec_sanitizer'],
    entry_points    = { 'console_scripts': [
                          "openapi_spec_sanitizer = openapi_spec_sanitizer.__main__:main"
                        ] },
    keywords        = 'toposort graph tolerant',
    project_urls    = {'Issue Tracker':
                         'https://github.com/DavidTurland/openapi-spec-sanitizer/issues',
                       'SetupTools'   :
                         'https://setuptools.pypa.io/en/latest/userguide/index.html',
                      },
    python_requires= '>=3',
)
