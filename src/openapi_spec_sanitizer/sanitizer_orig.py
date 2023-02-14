import oyaml as yaml
import collections
import copy
import re
import sys
import os
import pprint
import urllib.request
from enum import Enum
from packaging.version import parse as parse_version

class InvalidYamlException(Exception):
   def __init__(self,msg):
      super().__init__("InvalidYamlException: " + msg)

class DirtyYamlWarning(Exception):
   def __init__(self,msg):
      super().__init__("DirtyYamlWarning: " + msg)

class Stateful:
    def __init__(self,state):
        self._state = state
    def needs(self,state,msg):
        if(state.value < self._state.value):
            print(f"invalid state needs {state} but in {self._state},  {msg}")

class Loader(Stateful):
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
        self.path = None
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

    def load(self,file):
        self.yaml = yaml.load(file, Loader=self.loader)
        return self.yaml

    def load(self,file):
        from pathlib import Path
        regex = re.compile(r'^(?:http|ftp)s?://',re.IGNORECASE)
        print(f"looking in {os.getcwd()}")
        if ( Path(file).exists() and Path(file).is_file()):
            print(f"file exists {file}")
            self.load_path(file)
        elif re.match(regex, file) is not None:
            self.load_url(file)
        else:
            self.load_str(file)
        return self.yaml

class Analyzer(Stateful):

    class Entry:
        def __init__(self, tipe,path,line):
            self.tipe = tipe;
            self.path = path;
            self.line = line
        def __str__(self):
            return(f"{self.tipe}: Path: {self.path}, line: {self.line}")

    class Undefined:
        def __init__(self, path, referrers):
            self.path      = path;
            self.referrers = referrers
        def __str__(self):
            stringy = f"Path: {self.path}"
            for referrer in self.referrers:
                stringy += f"\n   {referrer}"
            return stringy

    class State(Enum):
        UNKNOWN   = 1
        LOADED    = 2
        PARSED    = 3
        SANITIZED = 4

    def __init__(self,args):
        super().__init__(self.State.UNKNOWN)
        self.document = None
        self.referrals   = collections.defaultdict(set)
        self.components = {}
        self.unused_components = None
        self.undefined_components = None

    def __str__(self):
        stringy  = f"------------------------ Analyzer State ----------------------------------------"
        stringy += f" referrals "
        stringy += pprint(self.referrals)
        stringy += f" Components "
        stringy += pprint(self.components)
        stringy += f" undefined_components "
        stringy += pprint(self.undefined_components)
        stringy += f" unused_components "
        stringy += pprint(self.unused_components)
        return stringy

    def _swagger_ver(self):
        self.needs(self.State.LOADED,"failed to load or load_str")
        if 'swagger' in self.document:
            self._version = float(self.document['swagger'])
        elif 'openapi' in self.document:
            self._version = float( parse_version(self.document['openapi']).major)
        else:
            raise InvalidYamlException("swagger or openapi key not found")

    def analyze(self,document):
        self.document = document
        self._swagger_ver()
        self.needs(self.State.LOADED,"failed to load or load_str")
        self._analyze(self.document,())
        self.get_undefined_components()
        self.get_unused_components()
        self._state = self.State.PARSED
        if(self.undefined_components):
            raise InvalidYamlException("Undefined elements")
        if self.unused_components:
            raise DirtyYamlWarning("Unused elements")

    def _analyze(self, dictionary, path):
        if type(dictionary) == list:
            for i, element in enumerate(dictionary):
                self._analyze( element, path+(i,) )
        elif type(dictionary) == dict:
            node_path = ''.join(['/' + str(node)  for node in path])
            line_no = dictionary.get('__line__',None)
            if(self._is_component(path)):
                self.components[node_path] = self.Entry('Component',node_path, line_no)
            for key, value in dictionary.items():
                if('$ref' == key):
                    # normalise ref and def: remove '#' from start of reference
                    def_path = dictionary[key][1:]
                    self.referrals[def_path].add(self.Entry("Referrer", node_path,line_no))
                elif '__line__' != key:
                    # SafeLineLoader adds __line__ element
                    self._analyze( dictionary[key], path+(key,))
                else:
                    # just a normal element, just an innocent element 
                    pass

    def get_undefined_components(self):
        self.needs(self.State.PARSED,"failed to load or load_str")
        if(self.undefined_components is None):
            self.undefined_components = { def_path : self.Undefined(def_path,referrers) 
                                           for def_path,referrers in self.referrals.items() 
                                           if def_path not in self.components and (0 < len(referrers))
                                         }
        return self.undefined_components

    def get_unused_components(self):
        self.needs(self.State.PARSED,"failed to load or load_str")
        if(self.unused_components is None):
            self.unused_components = {}
            changed = True
            iteration = 1;
            while changed:
                print (f"Iteration {iteration} " + ">" * 20 )
                changed = False
                iteration +=1
                for component_path, component in self.components.items():
                    if component_path not in self.referrals or not self.referrals[component_path]:
                        print(f"   Did not use component {component}")
                        self.unused_components[component_path] = component
                print("referrers of unused components")
                for referred_component_path, referrers in self.referrals.items():
                    referrers_to_be_removed = set()
                    for referrer in referrers:
                        for component_path, component in self.unused_components.items():
                            # referrer may be within an unused omponenent
                            if referrer.path.startswith(component_path):
                                print(f"Unused: {referrer} not used, referencing {component}")
                                referrers_to_be_removed.add(referrer)
                    referrers -= referrers_to_be_removed
                for referred_component_path, referrers in self.referrals.items():
                    if 0 == len(referrers) :
                        if(referred_component_path in self.undefined_components):
                            print(f"  Did not use undefined component path {referred_component_path}, by deduction")
                            # mark undefined as dirty
                            #self.undefined_components = None
                        elif referred_component_path not in self.unused_components:
                            component = self.components[referred_component_path]
                            print(f"  Did not use component {component}, by deduction, referred_component_path: {referred_component_path}")
                            self.unused_components[referred_component_path] = component
                            changed = True

        return self.unused_components

    def _is_component(self,path):
        self.needs(self.State.LOADED,"_is_component")
        if(   3.0 == self._version and
              3 == len(path) and
              'components' == path[0] and
              path[1] in ('parameters','requestBodies','responses','schemas','securitySchemas')):
            return True
        elif( 3.0 == self._version and
              2 == len(path) and
              path[0] in ('parameters','responses','definitions','securityDefinitions')):
            return True
        return False

class Sanitizer(Stateful):
    class SanitizeMode(Enum):
        DELETE    = 1
        TAG       = 2
        NONE      = 3

    class State(Enum):
        UNKNOWN   = 1
        LOADED    = 2
        PARSED    = 3
        SANITIZED = 4

    def __init__(self,args):
        super().__init__(self.State.UNKNOWN)
        self.sanitizing    = args.sanitize
        self.orig_yaml     = {}
        self.working_yaml  = {}
        if self.sanitizing:
            if("tag" == args.mode):
                self.sanitize_mode = self.SanitizeMode.TAG
                self.sanitize_tag  = args.tag
            elif ("delete" == args.mode):
                self.sanitize_mode = self.SanitizeMode.DELETE
        self._debug        = args.debug
        self.loader        = Loader(args)
        self.analyzer      = Analyzer(args)

    def dump(self,path):
        with open(path, 'w',encoding='utf-8') as file:
            yaml.dump(self.working_yaml, file,width=1000)

    def sanitize(self,file):
        self.orig_yaml = self.loader.load(file)
        self.analyzer.analyze(self.orig_yaml)
        if self.sanitizing:
            self.needs(self.State.LOADED,"will be sanitizing")
            self._sanitize(self.orig_yaml,())
        self._state = self.State.SANITIZED

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
            node.pop('__line__', None)

    def _sanitize_node(self,node):
        """ Assumes node is a dict! """
        if self.SanitizeMode.TAG == self.sanitize_mode:
            node[self.sanitize_tag] = True
        elif self.SanitizeMode.DELETE == self.sanitize_mode:
            del node

