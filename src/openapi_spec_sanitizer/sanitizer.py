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
__all__ = ['Sanitizer']

import sys
from enum import Enum
from pathlib import Path
import logging
import os
import oyaml as yaml

from .loader import Loader
from .stateful import Stateful
from .analyzer import Analyzer,State
from .exceptions import *

logger = logging.getLogger('openapi_spec_sanitizer')

class Sanitizer(Stateful):

    class SanitizeMode(Enum):
        DELETE    = 1
        TAG       = 2
        NONE      = 3

    def __init__(self,args):
        super().__init__(State.UNKNOWN)
        self.sanitizing      = args.sanitize
        self.output_filename = args.output
        self._debug          = args.debug
        self.warnings_are_ok = args.warnings_are_ok
        self.sanitize_mode   = self.SanitizeMode.NONE
        self.orig_yaml       = {}
        if self.sanitizing:
            if(args.tag is not None ):
                self.sanitize_mode = self.SanitizeMode.TAG
                self.sanitize_tag  = args.tag
            elif (args.delete):
                self.sanitize_mode = self.SanitizeMode.DELETE
        self.loader        = Loader(args)
        self.analyzer      = Analyzer(args)

    def report(self):
        return self.analyzer.report()

    def dump(self,path):
        self.at_least(State.LOADED,"dump")
        filename        = self.output_filename
        loader_filename = self.loader.get_filename()
        if filename is None:
            if loader_filename is None: 
                raise InvalidFileException()
            root, ext = os.path.splitext(loader_filename)
            filename = f"{root}.san{ext}"
        elif loader_filename is not None:
            if(loader_filename == filename):
                raise InvalidFileException(f"will not overwrite original file {filename}")
        if Path(filename).exists():
            raise InvalidFileException(f"will not overwrite existing file {filename}")
        logger.info(f"Main: dumping sanitized yaml to {filename}")
        with open(filename, 'w',encoding='utf-8') as file:
            yaml.dump(self.orig_yaml, file,width=1000)

    def sanitize(self,file):
        self.orig_yaml = self.loader.load(file)
        try:
            self.analyzer.analyze(self.orig_yaml)
        except Warning as e:

            if self.warnings_are_ok:
                logger.warning(f"Sanitizer: Tolerable issue when analyzing yaml: {e}")
            else:
                logger.warning(f"Sanitizer: Urecoverable issue when analyzing yaml: {e}")
                raise e
        except Unrecoverable as e:
            logger.error(f"Sanitizer: Urecoverable issue when analyzing yaml: {e}")
            raise e
        if self.sanitizing:
            logger.info(f"Sanitizing")
            root_path = ()
            self._sanitize(self.orig_yaml,root_path)
        self._state = State.SANITIZED

    def _sanitize(self, node, path):
        if type(node) == list:
            unused_nodes = []
            for i, element in enumerate(node):
                dest_path     = path+(i,)
                dest_path_str = ''.join(['/' + str(n)  for n in dest_path])
                unused_node   =  dest_path_str in self.analyzer.unused_components
                if unused_node:
                    print(f"Marking node {dest_path} as unused")
                    unused_nodes.append(i)
                self._sanitize( element, dest_path )
            for i in sorted(unused_nodes,reverse = True):
                self._sanitize_node(node[i])
            # remove bogus __line__
            node = [kv for kv in node if '__line__' not in kv]
        elif type(node) == dict:
            unused_nodes = set()
            for key, value in node.items():
                dest_path     = path+(key,)
                dest_path_str = ''.join(['/' + str(n)  for n in dest_path])
                unused_node   =  dest_path_str in self.analyzer.unused_components
                if unused_node:
                    unused_nodes.add(key)
                    print(f"Marking node {dest_path} as unused")
                self._sanitize( node[key], dest_path)
            for key in unused_nodes:
                self._sanitize_node(node[key])
            # remove bogus __line__                
            node.pop('__line__', None)

    def _sanitize_node(self,node):
        """ Assumes node is a dict! """
        if self.SanitizeMode.TAG == self.sanitize_mode:
            node[self.sanitize_tag] = True
        elif self.SanitizeMode.DELETE == self.sanitize_mode:
            del node

