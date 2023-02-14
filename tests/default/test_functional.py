#######################################################################
# Tests for openapi-spec-sanitizer
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
import oyaml as yaml
import unittest
import pprint
import sys
import re

class TestFunctional(unittest.TestCase):
    def test_url_parsing(self):
        regex = re.compile(r'^(?:http|ftp)s?://.*/(?P<filename>(?P<root>.*)(?P<ext>\.\w*))$',re.IGNORECASE)
        urls = [('https://raw.githubusercontent.com/OAI/OpenAPI-Specification/main/examples/v3.0/api-with-examples.yaml','api-with-examples', '.yaml','api-with-examples.yaml')]
        for url,root,ext,filename in urls:
            m = re.match(regex, url)
            self.assertIsNotNone(m)
            self.assertEqual(m.group('root'),root)
            self.assertEqual(m.group('ext'),ext)
            self.assertEqual(m.group('filename'),filename)
