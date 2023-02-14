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

__all__ = ['InvalidYamlException', 
           'DirtyYamlWarning',
           'UnsupportedYamlException',
           'InvalidFileException',
           'Warning',
           'Unrecoverable']

class Warning(Exception):
    pass

class Unrecoverable(Exception):
    pass

class InvalidYamlException(Unrecoverable):
   def __init__(self,msg):
      super().__init__("InvalidYamlException: " + msg)

class DirtyYamlWarning(Warning):
   def __init__(self,msg):
      super().__init__("DirtyYamlWarning: " + msg)

class UnsupportedYamlException(Unrecoverable):
   def __init__(self,msg):
      super().__init__("UnsupportedYamlException: " + msg)

class InvalidFileException(Unrecoverable):
   def __init__(self,msg=''):
      super().__init__("InvalidFileException: " + msg)      
