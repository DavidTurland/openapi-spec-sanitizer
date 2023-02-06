import yaml
import collections
from enum import Enum
from packaging.version import parse as parse_version

# Thanks https://stackoverflow.com/questions/13319067/parsing-yaml-return-with-line-number
class SafeLineLoader(yaml.loader.SafeLoader):
    def construct_mapping(self, node, deep=False):
        mapping = super(SafeLineLoader, self).construct_mapping(node, deep=deep)
        mapping['__line__'] = node.start_mark.line + 1
        return mapping

class State(Enum):
    UNKNOWN = 1
    LOADED  = 2
    PARSED  = 3

class Sanitizer:
    def __init__(self, referrals ={},definitions={},rewrite=False):
        self.referrals = collections.defaultdict(set)
        self.definitions = definitions
        self.unused_definitions = {}
        self.bank_yaml = {}
        self._version  = None
        self.debug     = False
        self._state   = State.UNKNOWN

    def needs(self,state,msg):
        if(state.value < self._state.value):
            print(f"invalid state {msg}")

    def load_str(self,yaml_str):
        self.bank_yaml = yaml.load(yaml_str, Loader=SafeLineLoader)
        self._state = State.LOADED
        self._swagger_ver()

    def load(self,path_in_str):
        with open(path_in_str, 'r',encoding='utf-8') as file:
            self.bank_yaml = yaml.load(file, Loader=SafeLineLoader)
            self._state   = State.LOADED
            self._swagger_ver()

    def walk(self):
        self.needs(State.LOADED,"failed to load or load_str")
        self._walk_spec(self.bank_yaml,())
        self._state = State.PARSED

    def _is_definition(self,path):
        self.needs(State.LOADED,"failed to load or load_str")
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

    def _walk_spec(self, dictionary, path):
        if type(dictionary) == list:
            for i, element in enumerate(dictionary):
                self._walk_spec( element, path+(i,) )
        elif type(dictionary) == dict:
            jp = ''.join(['/' + str(ele)  for ele in path])
            line_no = dictionary.get('__line__',None)
            if(self._is_definition(path)):
                self.definitions[jp] = {'__line__' : line_no}
            for key, value in dictionary.items():
                if('$ref' == key):
                    # remove '#' from start
                    def_path = dictionary[key][1:]
                    self.referrals[def_path].add((jp,line_no))
                elif '__line__' != key:
                    self._walk_spec( dictionary[key], path+(key,))

    def undefined_defs(self):
        self.needs(State.PARSED,"failed to load or load_str")
        for def_path, referrers in self.referrals.items():
            if def_path not in self.definitions:
                print(f"  Did not find definition for {def_path} referred ")

    def unused_defs(self):
        self.needs(State.PARSED,"failed to load or load_str")
        changed = True
        iteration = 1;
        while changed:
            print (f"Iteration {iteration} " + ">" * 20 )
            changed = False
            iteration +=1
            for definition, definition_meta in self.definitions.items():
                if definition not in self.referrals or not self.referrals[definition]:
                    print(f"   Did not use definition {definition}, line number {definition_meta['__line__']}")
                    self.unused_definitions[definition] = definition_meta
                    print(f"add unused_definitions {definition} line {definition_meta['__line__']}")
            for referred_definition, referrers in self.referrals.items():
                referrers_to_be_removed = set()
                for referrer in referrers:
                    for definition, definition_meta in self.unused_definitions.items():
                        if referrer[0].startswith(definition):
                            print(f"  Referrer{referrer} not used, referencing {referred_definition}, line number {definition_meta['__line__']}")
                            referrers_to_be_removed.add(referrer)
                referrers -= referrers_to_be_removed
                if not referrers:
                    print(f"Empty referrer so will not be using {referred_definition}")
            for referred_definition, referrers in self.referrals.items():
                if(0 == len(referrers) and (referred_definition not in self.unused_definitions)):
                    definition_meta = self.definitions[referred_definition]
                    print(f"  Did not use definition {referred_definition}, line number {definition_meta['__line__']}, by deduction")
                    self.unused_definitions[referred_definition] = definition_meta
                    print(f"add inferred unused_definitions {referred_definition} line {definition_meta['__line__']}")
                    changed = True
        for definition,definition_meta in self.unused_definitions.items():
            print(f" Not using {definition}, line number {definition_meta['__line__']}")
        return self.unused_definitions

    def _swagger_ver(self):
        self.needs(State.LOADED,"failed to load or load_str")
        if 'swagger' in self.bank_yaml:
            self._version = float(self.bank_yaml['swagger'])
        elif 'openapi' in self.bank_yaml:
            self._version = float( parse_version(self.bank_yaml['openapi']).major)

