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

import collections
import re
import logging
import pprint
from packaging.version import parse as parse_version
from enum import Enum

from .stateful import Stateful
from .entry import Entry
from .exceptions import *

logger = logging.getLogger('openapi_spec_sanitizer')

class State(Enum):
    UNKNOWN   = 1
    LOADED    = 2
    PARSED    = 3
    SANITIZED = 4

class Analyzer(Stateful):
    class Undefined:
        def __init__(self, path, referrers):
            self.path      = path
            self.referrers = referrers
        def __str__(self):
            stringy = f"Cmponent Path: {self.path}"
            for referrer in self.referrers:
                stringy += f"\n  Referrer: {referrer}"
            return stringy

    def __init__(self,args):
        super().__init__(State.UNKNOWN)
        self._debug     = args.debug
        self.document = None
        self.referrers   = collections.defaultdict(set)
        self.components = {}
        self.unused_components = None
        self.undefined_components = None

    def report(self):
        stringy  = "------------------------ Analyzer Report ----------------\n"
        if self._debug:
            if self.referrers is not None:
                stringy += "Referrers:\n"
                for referrer in self.referrers:
                    stringy += '  ' + pprint.pformat(referrer) + '\n'
            stringy += "Components: \n"
            for component in self.components:
                stringy += '  ' + pprint.pformat(component) + '\n'
        if self.undefined_components:
            stringy += "Undefined components \n"
            for undefined_component in self.undefined_components:
                stringy += '  ' + pprint.pformat(undefined_component) + '\n'
        if self.unused_components:
            stringy += "Uunused components \n"
            for key, unused_component in self.unused_components.items():
                stringy += f'  path: {key}\n'
                stringy += '         ' + pprint.pformat(unused_component) + '\n'
        stringy += "----------------------- ~Analyzer Report ----------------\n"            
        return stringy

    def _swagger_ver(self):
        self.needs(State.LOADED,"_swagger_ver")
        if 'swagger' in self.document:
            self._version = float(self.document['swagger'])
        elif 'openapi' in self.document:
            self._version = float( parse_version(self.document['openapi']).major)
        else:
            raise InvalidYamlException("swagger or openapi key not found")

    def analyze(self,document):
        # we may have analyzed so reset state
        self._state = State.LOADED
        self.document = document
        self._swagger_ver()
        root_path = ()
        self._analyze(self.document,root_path)
        self._state = State.PARSED
        self._capture()

        if(self.undefined_components):
            logger.debug(f"Analyzer failed with {len(self.undefined_components)} undefined_components")
            raise InvalidYamlException(f"Undefined elements: {','.join(self.undefined_components.keys())}")
        if self.unused_components:
            logger.debug(f"Analyzer failed with {len(self.unused_components)} unused_components")
            raise DirtyYamlWarning("Unused elements")

    def _ref_remote(self,value):
        regex = re.compile(r'^(.+\.yaml)',re.IGNORECASE)
        m = re.match(regex, value)
        if m:
            return m.group(1)
        return None

    def _get_node(self,node_path,tipe):
        if node_path in self.components:
            return self.components[node_path]
        node = Entry(tipe,node_path)
        self.components[node_path] = node
        return node

    def _analyze(self, dictionary, parent_path, parent_component = None):
        """ 
           parent_path       path to parent, a tuple of breadcrumbs
           parent_component  the component this is part of (if any)
        """
        if type(dictionary) == list:
            for i, element in enumerate(dictionary):
                self._analyze( element, parent_path+(i,),parent_component )
        elif type(dictionary) == dict:
            node_path = ''.join(['/' + str(node)  for node in parent_path])
            line_no   = dictionary.get('__line__',None)
            curr_parent_component = parent_component
            curr_node = None

            if(self._is_component(parent_path)):
                curr_node = self._get_node(node_path,'Component')
                curr_node.declare(line_no)
                if parent_component is not None:
                    raise InvalidYamlException(f"This {node_path} is a component, but a parent {parent_component} is a component")
                curr_parent_component = curr_node
                # implicit: this is a component
                curr_node.set_component(curr_parent_component)
            for key in dictionary.keys():
                if('$ref' == key):
                    value = dictionary[key]
                    if self._ref_remote(value):
                        raise UnsupportedYamlException(f"Unsupported Remote reference, node_path {node_path}, line_no {line_no}")
                    # normalise ref and def: remove '#' from start of reference
                    def_path = dictionary[key][1:]
                    component_node = self._get_node(def_path,'Component')
                    curr_node = self._get_node(node_path,'Referrer')
                    curr_node.declare(line_no)
                    curr_node.set_ref_path(def_path)
                    component_node.add_referrer(node_path,curr_node)
                    if curr_parent_component is not None:
                        curr_node.set_component(curr_parent_component)
                    self.referrers[def_path].add(curr_node)
                elif '__line__' != key:
                    # SafeLineLoader adds __line__ element
                    self._analyze( dictionary[key], parent_path+(key,),curr_parent_component)
                else:
                    # just a normal element, just an innocent element 
                    pass

    def _capture(self):
        self.at_least(State.PARSED,"_capture")

        self.undefined_components = { def_path : self.Undefined(def_path,component.referrers) 
                                       for def_path,component in self.components.items() 
                                       if component.is_required(set()) and not component.is_declared() and component.is_component()
                                    }

        self.unused_components = { def_path : component 
                                   for def_path,component in self.components.items() 
                                   if not component.is_required() and component.is_declared() and component.is_component()
                                 }

    def get_undefined_components(self):
        self.at_least(State.PARSED,"get_undefined_components")
        return self.undefined_components

    def get_unused_components(self):
        self.at_least(State.PARSED,"get_unused_components")
        return self.unused_components

    def _is_component(self,path):
        self.at_least(State.LOADED,"_is_component")

        if(  3.0 == self._version and
             3 == len(path) and
             'components' == path[0] and
              path[1] in ('parameters','requestBodies','responses','schemas','securitySchemas')):
            return True
        elif( 2.0 == self._version and
              2 == len(path) and
              path[0] in ('parameters','responses','definitions','securityDefinitions')):
            return True
        return False
