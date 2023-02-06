#######################################################################
# Tests for tolerant.toposort module.
# Copyright David Turland 2023
# Copyright 2014-2021 True Blade Systems, Inc.
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
#
# Notes:
# This is a modification of the original test_toposort
# 1 - package rename to tolerant.toposort
# 2 - data is now modified to remove self-referential elements
#
########################################################################
from pathlib import Path
import unittest

from openapi_spec_sanitizer.sanitizer import Sanitizer

class TestOpenbanking(unittest.TestCase):

    def test_openbanking(self):
        print("============================= test_openbanking")
        spec_dirs=[ "directory-api-specs",
                    "client-registration-api-specs/dist",
                    "read-write-api-specs/dist/openapi"
                  ]
        for spec_dir in spec_dirs:
            pathlist = Path(spec_dir).glob('*.yaml')
            for path in pathlist:
                path_in_str = str(path)
                walker = Sanitizer()
                walker.debug = True
                walker.load(path_in_str)
                walker.walk()
                walker.undefined_defs()
                walker.unused_defs()
        print("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ test_openbanking")

if __name__ == '__main__':
    main()
