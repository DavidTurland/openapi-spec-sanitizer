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
from yaml import load
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader
import unittest
import os
import urllib.request
from pathlib import Path
from openapi_spec_sanitizer.sanitizer import Sanitizer
from openapi_spec_sanitizer.exceptions import DirtyYamlWarning
from openapi_spec_sanitizer.argparser import ArgParser


class TestOpenBanking(unittest.TestCase):
    def test_openbanking(self):
        cache_dir = './tests/openbanking/.cache'
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        yaml_specs_file = "./tests/openbanking/openbanking_specs.yaml"
        extensions = ['.yaml', '.json']
        with open(yaml_specs_file, 'r', encoding='utf-8') as file:
            openapi_specs = load(file, Loader=Loader)
        for openapi_spec in openapi_specs:
            filename = openapi_spec['filename']
            root, ext = os.path.splitext(filename)
            for extension in extensions:
                url_root = openapi_spec['url']
                expected_unused = set(openapi_spec['unused_components'])

                cache_path = f"{cache_dir}/{root}{extension}"
                url_path = f"{url_root}/{root}{extension}"
                if not Path(cache_path).exists():
                    urllib.request.urlretrieve(url_path, cache_path)
                parser = ArgParser()
                args = parser.parse_args([cache_path])
                sanitizer = Sanitizer(args)
                if len(expected_unused):
                    with self.assertRaises(DirtyYamlWarning):
                        sanitizer.sanitize(cache_path)
                    self.assertSetEqual(set(list(sanitizer.analyzer.unused_components.keys())),
                                        expected_unused,
                                        "unused"
                                        )
                else:
                    sanitizer.sanitize(cache_path)
