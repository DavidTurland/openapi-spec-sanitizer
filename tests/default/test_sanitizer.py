#######################################################################
# Tests for openapi-spec-sanitizer
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
import oyaml as yaml
import unittest
from openapi_spec_sanitizer.sanitizer import Sanitizer
from openapi_spec_sanitizer.exceptions import InvalidYamlException, UnsupportedYamlException
from openapi_spec_sanitizer.argparser import ArgParser


class TestSanitizer(unittest.TestCase):

    def test_api_with_examples_yaml_file(self):
        """
          snapshot (14/2/23) cached locally so tests can run locally
        """
        # src_url = 'https://raw.githubusercontent.com/OAI/OpenAPI-Specification/main/examples/v3.0/api-with-examples.yaml'
        file = "./tests/api-with-examples.yaml"
        # but can make it dynamic:
        # import urllib.request
        # urllib.request.urlretrieve(src_url, file)
        parser = ArgParser()
        args = parser.parse_args([file])
        sanitizer = Sanitizer(args)
        sanitizer.sanitize(file)

    def test_remote_ref(self):
        test_yaml = """
openapi: 3.0.0
paths:
  /wibble:
    post:
      summary: wobble
      requestBody:
        $ref: '../floob.yaml/components/requestBodies/requestBodyMissing'
      responses:
        '201':
          $ref: '#/components/responses/responseA'
components:
  responses:
    responseA:
      description: Created
      headers:
        responseHeader:
          schema:
            type: "string"
  schemas:
"""
        parser = ArgParser()
        args = parser.parse_args(['--yaml', test_yaml])
        sanitizer = Sanitizer(args)

        with self.assertRaises(UnsupportedYamlException):
            sanitizer.sanitize(test_yaml)

    def test_remote_ref_json(self):
        test_yaml = """
{
    "openapi": "3.0.0",
    "paths": {
        "/wibble": {
            "post": {
                "summary": "wobble",
                "requestBody": {
                    "$ref": "../floob.yaml/components/requestBodies/requestBodyMissing"
                },
                "responses": {
                    "201": {
                        "$ref": "#/components/responses/responseA"
                    }
                }
            }
        }
    },
    "components": {
        "responses": {
            "responseA": {
                "description": "Created",
                "headers": {
                    "responseHeader": {
                        "schema": {
                            "type": "string"
                        }
                    }
                }
            }
        },
        "schemas": null
    }
}
"""
        parser = ArgParser()
        args = parser.parse_args(['--json', test_yaml])
        sanitizer = Sanitizer(args)

        with self.assertRaises(UnsupportedYamlException):
            sanitizer.sanitize(test_yaml)

    def test_bogus_yaml(self):
        """
        https://pyyaml.org/wiki/PyYAMLDocumentation#loading-yaml
        """
        bogus_yamls = ["unbalanced blackets: ]["]
        parser = ArgParser()
        for bogus_yaml in bogus_yamls:
            args = parser.parse_args(['--yaml', bogus_yaml])
            sanitizer = Sanitizer(args)

            with self.assertRaises(yaml.parser.ParserError):
                sanitizer.sanitize(bogus_yaml)

    def test_openapi_versions(self):

        versions = [
                     ('openapi', '3.0.0',   True, None),
                     ('openapi', '.3.0.0',  False, InvalidYamlException),
                     ('openapi', 'wibble',  False, InvalidYamlException),
                     ('openapi', '4.0.0',   False, InvalidYamlException),
                     ('swagger', '2.0',     False, InvalidYamlException),
                     ('swagger', '1.9',     False, InvalidYamlException),
                     ('swagger', '3.0',     False, InvalidYamlException),
                     ('swagger', 'wibble',  False, InvalidYamlException),
                     ('flooby', 'dooby',   False, InvalidYamlException)
                    ]

        for brand, version, ok, exception in versions:
            test_yaml = """
{brand}: {version}
paths:
  /wibble:
    post:
      summary: wobble
      requestBody:
        $ref: '#/components/requestBodies/requestBody'
components:
  parameters:
  requestBodies:
    requestBody:
      description: requestBodyAUnused description
      required: true
      content:
        application/json:
          schema:
            type: string
  responses:
  schemas:
""".format(version=version, brand=brand)
            parser = ArgParser()
            args = parser.parse_args(['--yaml', test_yaml])
            sanitizer = Sanitizer(args)
            if ok:
                sanitizer.sanitize(test_yaml)
            else:
                with self.assertRaises(exception, msg="THis doesnty work"):
                    sanitizer.sanitize(test_yaml)

    def test_simple(self):
        test_yaml = """
openapi: 3.0.0
paths:
  /wibble:
    post:
      summary: wobble
      requestBody:
        $ref: '#/components/requestBodies/requestBodyMissingRequired'
      responses:
        '201':
          $ref: '#/components/responses/responseA'
components:
  parameters:
  requestBodies:
    requestBodyAUnused:
      description: requestBodyAUnused description
      required: true
      content:
        application/vnd.openbanking.directory.authorisationserver-v2+json:
          schema:
            $ref: '#/components/schemas/schemaAbMissingUnused'
  responses:
    responseA:
      description: responseA
      headers:
        OB-Request-Id:
          schema:
            $ref: '#/components/schemas/schemaPlainMissingUnused'
  schemas:
"""
        parser = ArgParser()
        args = parser.parse_args(['--yaml', test_yaml])
        sanitizer = Sanitizer(args)

        with self.assertRaises(InvalidYamlException):
            sanitizer.sanitize(test_yaml)

        expected_unused = {'/components/requestBodies/requestBodyAUnused'}
        self.assertSetEqual(set(list(sanitizer.analyzer.unused_components.keys())),
                            expected_unused,
                            "expected_unused"
                            )
        expected_undefined = {'/components/requestBodies/requestBodyMissingRequired',
                              '/components/schemas/schemaPlainMissingUnused'
                              }
        self.assertSetEqual(set(list(sanitizer.analyzer.get_undefined_components().keys())),
                            expected_undefined,
                            "expected_undefined"
                            )

    def test_simple_json(self):
        test_yaml = """
{
    "openapi": "3.0.0",
    "paths": {
        "/wibble": {
            "post": {
                "summary": "wobble",
                "requestBody": {
                    "$ref": "#/components/requestBodies/requestBodyMissingRequired"
                },
                "responses": {
                    "201": {
                        "$ref": "#/components/responses/responseA"
                    }
                }
            }
        }
    },
    "components": {
        "parameters": null,
        "requestBodies": {
            "requestBodyAUnused": {
                "description": "requestBodyAUnused description",
                "required": true,
                "content": {
                    "application/vnd.openbanking.directory.authorisationserver-v2+json": {
                        "schema": {
                            "$ref": "#/components/schemas/schemaAbMissingUnused"
                        }
                    }
                }
            }
        },
        "responses": {
            "responseA": {
                "description": "responseA",
                "headers": {
                    "OB-Request-Id": {
                        "schema": {
                            "$ref": "#/components/schemas/schemaPlainMissingUnused"
                        }
                    }
                }
            }
        },
        "schemas": null
    }
}
"""
        parser = ArgParser()
        args = parser.parse_args(['--json', test_yaml])
        sanitizer = Sanitizer(args)

        with self.assertRaises(InvalidYamlException):
            sanitizer.sanitize(test_yaml)

        expected_unused = {'/components/requestBodies/requestBodyAUnused'}
        self.assertSetEqual(set(list(sanitizer.analyzer.unused_components.keys())),
                            expected_unused,
                            "expected_unused"
                            )
        expected_undefined = {'/components/requestBodies/requestBodyMissingRequired',
                              '/components/schemas/schemaPlainMissingUnused'
                              }
        self.assertSetEqual(set(list(sanitizer.analyzer.get_undefined_components().keys())),
                            expected_undefined,
                            "expected_undefined"
                            )

    def test_less_simple(self):
        test_yaml = """
openapi: 3.0.0
paths:
  '/wibble':
    post:
      summary: wobble
      requestBody:
        $ref: '#/components/requestBodies/requestBodyARequired'
      responses:
        '201':
          $ref: '#/components/responses/responseARequired'
        '400':
          $ref: '#/components/responses/responseBRequired'
        '401':
          $ref: '#/components/responses/responseCRequired'
        '402':
          $ref: '#/components/responses/undefinedA'
components:
  parameters:
    unusedParameter:
      name: unusedParameter
      description: An unused parameter
      in: path
      required: true
      schema:
        $ref: '#/components/schemas/schemaPlain'
  requestBodies:
    requestBodyARequired:
      description: used by /wibble/post/requestBody
      required: true
      content:
        application/vnd.openbanking.directory.authorisationserver-v2+json:
          schema:
            $ref: '#/components/schemas/schemaAB'
  responses:
    responseARequired:
      description: Used by /wibble/responses/201
      headers:
        OB-Request-Id:
          schema:
            $ref: '#/components/schemas/schemaPlain'
    responseBRequired:
      description:  Used by /wibble/responses/400
      headers:
        OB-Request-Id:
          schema:
            $ref: '#/components/schemas/schemaPlain'
    responseCRequired:
      description: Used by /wibble/responses/401
      headers:
        OB-Request-Id:
          schema:
            $ref: '#/components/schemas/schemaC'
  schemas:
    schemaA:
      type: array
      description:  Unused
      items:
        $ref: '#/components/schemas/schemaAB'
    schemaAB:
      type: array
      description:  used by the requestBodyARequired and the unused /schemas/schemaA
      items:
        $ref: '#/components/schemas/schemaAC'
    schemaAC:
      type: array
      description:  used but by the unused /schemas/schemaA
      items:
        $ref: '#/components/schemas/schemaC'
    schemaC:
      type: array
      description:  Used by /reponses/responseC
      items:
        $ref: '#/components/schemas/schemaPlain'
    schemaPlain:
      type: array
      description:  Used by various
      items:
        type: string
"""
        parser = ArgParser()
        args = parser.parse_args(['--yaml', test_yaml])
        sanitizer = Sanitizer(args)
        with self.assertRaises(InvalidYamlException):
            sanitizer.sanitize(test_yaml)
        expected_unused = {'/components/schemas/schemaA',
                           '/components/parameters/unusedParameter'
                           }
        self.assertSetEqual(set(list(sanitizer.analyzer.unused_components.keys())),
                            expected_unused,
                            "unused"
                            )
        expected_undefined = {'/components/responses/undefinedA'}
        self.assertSetEqual(set(list(sanitizer.analyzer.undefined_components.keys())),
                            expected_undefined,
                            "expected_undefined"
                            )

    def test_less_simple_file(self):
        file = "./tests/less_simple.yaml"
        parser = ArgParser()
        args = parser.parse_args([file])
        sanitizer = Sanitizer(args)
        with self.assertRaises(InvalidYamlException):
            sanitizer.sanitize(file)
        expected_unused = {'/components/schemas/schemaA',
                           '/components/parameters/unusedParameter'
                           }
        self.assertSetEqual(set(list(sanitizer.analyzer.unused_components.keys())),
                            expected_unused,
                            "unused"
                            )
        expected_undefined = {'/components/responses/undefinedA'}
        self.assertSetEqual(set(list(sanitizer.analyzer.undefined_components.keys())),
                            expected_undefined,
                            "expected_undefined"
                            )

    def test_less_simple_file_json(self):
        file = "./tests/less_simple.json"
        parser = ArgParser()
        args = parser.parse_args([file])
        sanitizer = Sanitizer(args)
        with self.assertRaises(InvalidYamlException):
            sanitizer.sanitize(file)
        expected_unused = {'/components/schemas/schemaA',
                           '/components/parameters/unusedParameter'
                           }
        self.assertSetEqual(set(list(sanitizer.analyzer.unused_components.keys())),
                            expected_unused,
                            "unused"
                            )
        expected_undefined = {'/components/responses/undefinedA'}
        self.assertSetEqual(set(list(sanitizer.analyzer.undefined_components.keys())),
                            expected_undefined,
                            "expected_undefined"
                            )
