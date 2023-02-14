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

__all__=["Entry"]

class Entry:
    def __init__(self, tipe,node_path,line = None):
        self.tipe = tipe;
        self.node_path = node_path;
        self.line = line
        # self.ref = None
        self.ref_path = None
        self.referrers = {}   # node_path : Entry
        self.component = None # the component this Entry is under
        self.declared = False
        self.required = None

    def __repr__(self):
        return(f"Type: {self.tipe}, path: {self.node_path}, line: {self.line}, is component? {self.is_component()}, is declared? {self.declared}, is required? {self.required}")

    def is_declared(self):
        return self.declared

    def set_ref_path(self,ref_path):
        self.ref_path = ref_path
    
    def declare(self,line):
        self.line = line
        self.declared = True

    def set_component(self,component):
        self.component = component

    def is_part_of_component(self):
        return self.component is not None
        
    def is_component(self):
        return self.tipe == 'Component'
        
    def add_referrer(self,node_path,node):
        self.referrers[node_path] = node
        
    def is_required(self, cache = set()):
        if self.required is not None:
            return self.required
        if self.is_component():
            pass
        elif self.is_part_of_component():
            if self.component.node_path not in cache:
                cache.add(self.component.node_path)
                if self.component.is_required(cache):
                    self.required = True
                    return self.required
        else:
            self.required = True
            return self.required
        for referrer_path, referrer in self.referrers.items():
            if referrer.node_path not in cache:
                cache.add(referrer.node_path)
                if referrer.is_required(cache):
                    self.required = True
                    return self.required
        self.required = False
        return self.required
