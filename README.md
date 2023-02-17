![python_package](https://github.com/DavidTurland/openapi-spec-sanitizer/actions/workflows/python_package.yaml/badge.svg)
# openapi-spec-sanitizer

A Sanitizer for [OpenAPI](https://www.openapis.org/) YAML, or JSON, spec files

## Description

Offers a CLI, or simple API, to detect, report, and, optionally, fix unused components in OpenAPI specifications

* Detects unused, or undefined, components in Swagger (2.0) and OpenAPI (3.*) (YAML or json) specifications
* It can _sanitize_ discovered unused components, either by:
    - deleting the component
    - or adding a new tag to the component
* Sanitised YAML, or json, is stored to file
* OpenAPI/Swagger Spec files can be loaded from URI or file
* It always tries not to overwrite existing files(yay!)
* It detects (unsupported so far) remote references and politely gives up

This package was written with a [single purpose](#tests-some-of-the-openbanking-specification) in mind, and makes no claims other than proving _quite_ useful for that particular purpose.

Hopefully it will find a more general use.

## TODO
It doesn't do many things, but of note it might be useful to(most-likely first):
- ~~Add support for JSON-format Specification~~
- Add support for remote references, which depends on:
- Add support for multiple files
- Add support for caching remote (url) specifications to file

## Author
David Turland, david@turland.org

## Install
From PyPi:
```bash
pip install openapi-spec-sanitizer
```

From source:
```bash
python3 -m pip install
# or 
python3 -m pip install --user
```

## Usage
```bash
usage: openapi_spec_sanitizer [-h] [-c CACHEDIR] [-s] [-t TAG | -r]
                              [-o OUTPUT] [-l] [-v] [-g] [--version]
                              filename

Sanitize OpenAPI.

options:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        output file name for sanitized YAML
  -l, --lax             YAML, or JSON, syntax warnings are tolerable
  -v, --verbose
  -g, --debug
  --version             show the version number and exit

YAML, or JSON, Loading Options:
  filename              OpenAPI specification: file path or url (YAML, or JSON)

Sanitizing Options:
  -s, --sanitize        Attempt to sanitize spec file (default False)
  -t TAG, --tag TAG     sanitize mode is to tag component
  -r, --remove          Sanitize mode is to remove component
```

## Examples

### Testing for Unused and Undefined Component detection
```bash
openapi_spec_sanitizer tests/simple.yaml -l
```

```bash
------------------------ Analyzer Report ----------------
Undefined components
  '/components/requestBodies/requestBodyMissingRequired'
  '/components/schemas/schemaPlainMissingUnused'
Uunused components
  path: /components/requestBodies/requestBodyAUnused
         Type: Component, path: /components/requestBodies/requestBodyAUnused, line: 15, is component? True, is declared? True, is required? False
----------------------- ~Analyzer Report ----------------
```

### Sanitizing Unused components

Here we have an OpenAPI spec with an unused component,`/components/requestBodies/requestBodyAUnused`
```yaml
openapi: 3.0.0
paths:
  /wibble:
    post:
      summary: wobble
      requestBody:
        application/json:
          schema:
            type: "string"
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
        application/json:
          schema:
            type: "string"
  responses:
    responseA:
      description: responseA
      headers:
        Floob:
          schema:
            type: "string"
```

Running `openapi_spec_sanitizer` with `-s` to sanitize  
**NOTE** the default mode is to tag unused components with `unused`
```bash
openapi_spec_sanitizer.exe tests/simple_unused.yaml -s
```

```cpp
...
Main: dumping sanitized YAML to tests/simple_unused.san.yaml
------------------------ Analyzer Report ----------------
Uunused components
  path: /components/requestBodies/requestBodyAUnused
         Type: Component, path: /components/requestBodies/requestBodyAUnused, line: 17, is component? True, is declared? True, is required? False
----------------------- ~Analyzer Report ----------------
```

Yields this sanitized YAML:  
**note** the unused component tagged with `unused`
```yaml
openapi: 3.0.0
paths:
  /wibble:
    post:
      summary: wobble
      requestBody:
        application/json:
          schema:
            type: string
      responses:
        '201':
          $ref: '#/components/responses/responseA'
components:
  parameters: null
  requestBodies:
    requestBodyAUnused:
      description: requestBodyAUnused description
      required: true
      content:
        application/json:
          schema:
            type: string
      unused: true
  responses:
    responseA:
      description: responseA
      headers:
        Floob:
          schema:
            type: string
```

## Tests

### Basic Testing

```bash
pytest
```

### OpenBanking Specification Tests
Tests some of the OpenAPI spec files from the [OpenBanking](https://github.com/OpenBankingUK) Official Open Banking UK API Standards  

And yes (as of 14/2/23) there are unused components...  
**NOTE:**
- These tests are not run as part of python setuptools 
- Remote spec files are cached once and used locally
```bash
pytest tests/openbanking
```
# Attributions
[OpenAPI Initiative OpenAPI-Specification](https://github.com/OAI/OpenAPI-Specification) - A snapshot of one of their sample OpenAPI spec files,[api-with-examples.yaml](https://raw.githubusercontent.com/OAI/OpenAPI-Specification/main/examples/v3.0/api-with-examples.yaml), is stored in this repo, and 
is used in one of the unit tests (It passes BTW :-) )
