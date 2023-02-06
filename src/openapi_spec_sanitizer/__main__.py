from .sanitizer import Sanitizer
import argparse
# python __main__.py --correct ../../../read-write-api-specs/dist/openapi/account-info-openapi.yaml

def main():
    parser = argparse.ArgumentParser(description='Sanitize OpenAPI.')
    parser.add_argument('filename',
                        help="openapi specification path (yaml) ")           # positional argument
    parser.add_argument('-s', '--sanitize',
                        action='store_true',
                        help="Attempt to sanitize spec file (default False) "
                        )  # on/off flag
    parser.add_argument("-o", "--output", type=str,
                        help="output file for sanitized (default is input + '.san')")
    parser.add_argument('-v', '--verbose',
                        action='store_true')  # on/off flag
    parser.add_argument('-g', '--debug',
                        action='store_true')  # on/off flag

    args = parser.parse_args()
    print(args.filename, args.sanitize, args.verbose)
    walker = Sanitizer(rewrite=args.sanitize)
    walker.debug = args.debug
    walker.load(args.filename)
    walker.walk()
    walker.undefined_defs()
    walker.unused_defs()

if __name__ == '__main__':
    main()
