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

__all__ = ['Loader']

import re
import oyaml as yaml
import urllib.request
from pathlib import Path

class Loader:
    # Thanks https://stackoverflow.com/questions/13319067/parsing-yaml-return-with-line-number
    class SafeLineLoader(yaml.loader.SafeLoader):
        def construct_mapping(self, node, deep=False):
            mapping = super(Loader.SafeLineLoader, self).construct_mapping(node, deep=deep)
            mapping['__line__'] = node.start_mark.line + 1
            return mapping
    class FullLineLoader(yaml.loader.FullLoader):
        def construct_mapping(self, node, deep=False):
            mapping = super(Loader.FullLineLoader, self).construct_mapping(node, deep=deep)
            mapping['__line__'] = node.start_mark.line + 1
            return mapping

    def __init__(self, args):
        self.sanitize = args.sanitize
        self.filename = None
        self.yaml = None
        self.loader = self.FullLineLoader if self.sanitize else self.SafeLineLoader

    def load_url(self,url):
        with urllib.request.urlopen(url) as file:
                self.yaml = yaml.load(file, Loader=self.SafeLineLoader)

    def load_str(self,yaml_str):
        self.yaml = yaml.load(yaml_str, Loader=self.loader)

    def load_path(self,file_path):
        with open(file_path, 'r',encoding='utf-8') as file:
            self.yaml = yaml.load(file, Loader=self.loader)
        self.filename = file_path

    def load(self,file):
        regex = re.compile(r'^(?:http|ftp)s?://',re.IGNORECASE)
        if ( Path(file).exists() and Path(file).is_file()):
            self.load_path(file)
        elif re.match(regex, file) is not None:
            self.load_url(file)
        else:
            self.load_str(file)
        return self.yaml

    def get_filename(self):
        """
          not all routes yield a filename
        """
        return self.filename
