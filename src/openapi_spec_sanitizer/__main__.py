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

import logging
import sys

from .sanitizer import Sanitizer
from .exceptions import DirtyYamlWarning,InvalidYamlException,Warning,Unrecoverable
from .ArgParser import ArgParser

def main():
    parser = ArgParser()
    args = parser.parse_args()
    logger = logging.getLogger('openapi_spec_sanitizer')
    console = logging.StreamHandler()
    if args.debug:
        logger.setLevel(logging.DEBUG)
        console.setLevel(logging.DEBUG)
    elif args.quiet:
        logger.setLevel(logging.WARNING)
        console.setLevel(logging.WARNING)
    else:
        logger.setLevel(logging.INFO)
        console.setLevel(logging.INFO)
    logger.addHandler(console)
    logger.info(f"filename   : {args.filename}")
    logger.info(f"sanitizing : {args.sanitize}")
    sanitizer = Sanitizer(args)
    epitaph =  ''
    try:
        sanitizer.sanitize(args.filename)
        sanitizer.dump("test.yaml")
    except DirtyYamlWarning as e:
        # these don't percolate up (yet!)
        print(f"Main: Tolerable issue with {e}")
    except Unrecoverable as e:
        epitaph = ' with errors'
        print(f"Main: Unrecoverable error with {e}")
    logger.info(sanitizer.report())
    logger.info(f"finished{epitaph}")

if __name__ == '__main__':
    main()
