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
import json
import os
import urllib.request
from pathlib import Path
from enum import Enum
from .exceptions import InvalidFileException


class OpenapiFormat(Enum):
    YAML = 1
    JSON = 2
    NONE = 3


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
        self.document = None
        self.default_openapi_format = OpenapiFormat.NONE
        if args.yaml:
            self.default_openapi_format = OpenapiFormat.YAML
        elif args.json:
            self.default_openapi_format = OpenapiFormat.JSON
        # might regret loader driving this....
        self.openapi_format = OpenapiFormat.NONE
        self.loader = self.FullLineLoader if self.sanitize else self.SafeLineLoader

    def load_url(self, url):
        with urllib.request.urlopen(url) as file:
            if OpenapiFormat.YAML == self.openapi_format:
                self.document = yaml.load(file, Loader=self.SafeLineLoader)
            elif OpenapiFormat.JSON == self.openapi_format:
                file_contents = file.read()
                self.document = json.loads(file_contents)
        return self.document

    def load_str(self, yaml_str):
        self.document = yaml.load(yaml_str, Loader=self.loader)
        return self.document

    def _yaml_format(self, name, openapi_fmt=None):
        if name is None:
            if openapi_fmt is not OpenapiFormat.NONE:
                self.openapi_format = openapi_fmt
            else:
                raise InvalidFileException("Uanble to determine openapi format")
        else:
            root, ext = os.path.splitext(name)
            if ext == '.yaml':
                self.openapi_format = OpenapiFormat.YAML
            elif ext == '.json':
                self.openapi_format = OpenapiFormat.JSON
            else:
                raise InvalidFileException("Uanble to determine openapi format")
        return self.openapi_format

    def load_path(self, file_path):

        with open(file_path, 'r', encoding='utf-8') as file:
            if OpenapiFormat.YAML == self.openapi_format:
                self.document = yaml.load(file, Loader=self.loader)
            elif OpenapiFormat.JSON == self.openapi_format:
                file_contents = file.read()
                self.document = json.loads(file_contents)
        self.filename = file_path
        return self.document

    def load(self, file):
        # TODO make this a factory
        if (Path(file).exists() and Path(file).is_file()):
            self._yaml_format(file)
            return self.load_path(file)
        regex = re.compile(r'^(?:http|ftp)s?://.*/(?P<filename>(?P<root>.*)(?P<ext>\.\w*))$', re.IGNORECASE)
        m = re.match(regex, file)
        if m is not None:
            self._yaml_format(m.group('filename'))
            return self.load_url(file)

        # only use default format on strings
        self._yaml_format(None, self.default_openapi_format)
        self.load_str(file)
        return self.document

    def get_openapi_format(self):
        """
          not all routes yield a filename
        """
        return self.openapi_format

    def get_filename(self):
        """
          not all routes yield a filename
        """
        return self.filename
