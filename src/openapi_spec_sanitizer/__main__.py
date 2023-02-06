from sanitizer import Sanitizer
import argparse
# python __main__.py --correct ../../../read-write-api-specs/dist/openapi/account-info-openapi.yaml

def main():
    parser = argparse.ArgumentParser(description='Sanitize OpenAPI.')
    parser.add_argument('filename')           # positional argument
    parser.add_argument('-v', '--verbose',
                    action='store_true')  # on/off flag
    parser.add_argument('-c', '--correct',
                    action='store_true')  # on/off flag
    args = parser.parse_args()
    print(args.filename, args.correct, args.verbose)
    walker = Sanitizer(rewrite=args.correct)
    walker.debug = True
    walker.load(args.filename)
    walker.walk()
    walker.undefined_defs()
    walker.unused_defs()

if __name__ == '__main__':
    main()
