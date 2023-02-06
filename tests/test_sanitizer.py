#######################################################################
# Tests for tolerant.toposort module.
# Copyright David Turland 2023
# Copyright 2014-2021 True Blade Systems, Inc.
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
#
# Notes:
# This is a modification of the original test_toposort
# 1 - package rename to tolerant.toposort
# 2 - data is now modified to remove self-referential elements
#
########################################################################

import unittest

from openapi_spec_sanitizer.sanitizer import Sanitizer

class TestCase(unittest.TestCase):
    def test_simple(self):
        self.assertEqual(1,1 )

    def test_objects(self):
        test_yaml = """
openapi: 3.0.0
paths:
  '/wibble':
    post:
      summary: wobble
      requestBody:
        $ref: '#/components/requestBodies/requestBodyA'
      responses:
        '201':
          $ref: '#/components/responses/responseA'
        '400':
          $ref: '#/components/responses/responseB'
        '401':
          $ref: '#/components/responses/responseC'

components:
  parameters:
    unusedParameter:
      name: unusedParameter
      description: The authorisation server Id
      in: path
      required: true
      schema:
        $ref: '#/components/schemas/schemaPlain'
  requestBodies:
    requestBodyA:
      description: requestBodyA description
      required: true
      content:
        application/vnd.openbanking.directory.authorisationserver-v2+json:
          schema:
            $ref: '#/components/schemas/schemaAB'
  responses:
    responseA:
      description: Created
      headers:
        OB-Request-Id:
          schema:
            $ref: '#/components/schemas/schemaPlain'
    responseB:
      description: Created
      headers:
        OB-Request-Id:
          schema:
            $ref: '#/components/schemas/schemaPlain'
    responseC:
      description: Created
      headers:
        OB-Request-Id:
          schema:
            $ref: '#/components/schemas/schemaC'
  schemas:
    schemaA:
      type: array
      items:
        $ref: '#/components/schemas/schemaAB'
    schemaAB:
      type: array
      items:
        $ref: '#/components/schemas/schemaAC'
    schemaAC:
      type: array
      items:
        $ref: '#/components/schemas/schemaC'
    schemaC:
      type: array
      items:
        $ref: '#/components/schemas/schemaPlain'
    schemaPlain:
      type: array
      items:
        type: string
"""

        test_referrals = {
          # referred_definition          referrer (path)
          '#/components/schemas/defg' : {'/components/schemas/deff/properties/SoftwareStatements/items'}, '#/components/schemas/defa' : {'/patha',
                                         '/pathb'},
          '#/components/schemas/defb' : {'/pathc',
                                         '/pathd',
                                         '/components/schemas/defc/content/text/plain/schema'},
          '#/components/schemas/defc' : {'/pathe',
                                         '/pathf'},
          '#/components/schemas/defe' : {'/components/schemas/defd/content/text/plain/schema',
                                         '/pathg'},
          '#/components/schemas/deff' : {'/components/schemas/defd/properties/SoftwareStatements/items'}
          }
        test_definitions = {
         # definition                  definition_path
         '#/components/schemas/defa' : '/components/schemas/defa',
         '#/components/schemas/defb' : '/components/schemas/defb',
         '#/components/schemas/defc' : '/components/schemas/defc',
         '#/components/schemas/defd' : '/components/schemas/defd',       # unused
         '#/components/schemas/defe' : '/components/schemas/defe',       # unused
         '#/components/schemas/deff' : '/components/schemas/deff',       # unused
         '#/components/schemas/defg' : '/components/schemas/defg'       # unused
         }
        walker = Sanitizer()
        walker.load_str(test_yaml)
        walker.walk()
        walker.undefined_defs()
        walker.unused_defs()
