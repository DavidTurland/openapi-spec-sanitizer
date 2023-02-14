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

import argparse

from . import __version__

class ArgParser():
    def __init__(self):
        parser = argparse.ArgumentParser(description='Sanitize OpenAPI.')
        self.argParser = parser
        load_group = parser.add_argument_group('Yaml Loading Options')
        load_group.add_argument('filename',
                            help="openapi specification: file path or url (yaml-only) ")
        # TODO
        # load_group.add_argument("-c", "--cache", dest = 'cachedir',type=str,
        #                    help="cache remote files (loaded from from url) locally")

        sanitizing_group = parser.add_argument_group('Sanitizing Options')
        sanitizing_group.add_argument('-s', '--sanitize',
                            action='store_true',
                            help="Attempt to sanitize spec file (default False) "
                            )

        mod_group = sanitizing_group.add_mutually_exclusive_group()
        mod_group.add_argument('-t', '--tag',
                            type=str,
                            default = "unused",
                            help="sanitize mode is to tag component"
                            )  
        mod_group.add_argument('-r', '--remove',
                            dest='delete',
                            action='store_true', 
                            help="Sanitize mode is to remove component"
                            )

        parser.add_argument("-o", "--output", type=str,
                            help="output file name for sanitized YAML")
        parser.add_argument('-l', '--lax',
                            dest='warnings_are_ok',
                            action='store_true',
                            help='Yaml syntax warnings are tolerable')
        parser.add_argument('-g', '--debug',
                            action='store_true')
        parser.add_argument('-q', '--quiet',
                            action='store_true')
        parser.add_argument('--version', action='version',
                            version='%(prog)s {}'.format(__version__),
                            help='show the version number and exit')

    def parse_args(self, args=None, namespace=None):
        return self.argParser.parse_args(args,namespace)
