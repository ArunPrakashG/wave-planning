"""Verify changed paths stay inside a phase's owned globs.

Usage: git diff --name-only <base>...<branch> | python3 check_owned.py --owns 'src/a/**' 'tests/a/**'
Reads one path per line on stdin. Exit 0 if every path matches an owned glob,
exit 1 (and list the violations on stdout) otherwise.
"""
import argparse
import sys

from globs import matches


def violations(paths, owns):
    return [p for p in paths if not any(matches(glob, p) for glob in owns)]


def main(argv=None, stdin=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owns", nargs="+", required=True, help="owned globs")
    args = parser.parse_args(argv)
    lines = (stdin or sys.stdin).read().splitlines()
    paths = [line.strip() for line in lines if line.strip()]
    bad = violations(paths, args.owns)
    for path in bad:
        print(f"NOT-OWNED {path}")
    if bad:
        return 1
    print(f"OK {len(paths)} path(s) within owned globs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
