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
__all__ = ['Stateful']
class Stateful:
    def __init__(self,state):
        self._state = state
    def needs(self,state,msg):
        if(state.value != self._state.value):
            print(f"Invalid state needs to be {state} {state.value} but in {self._state}{self._state.value},  {msg}")
    def at_least(self,state,msg):
        if(state.value > self._state.value):
            print(f"Invalid state needs to be at least {state} {state.value} but in {self._state}{self._state.value},  {msg}")
    def get_state():
        return self._state
