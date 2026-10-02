"""Path-glob helpers for ownership checks.

Glob dialect: `*` matches within one path segment, `**` matches across segments,
`**/` matches zero or more directories, `?` matches one non-slash character.
No character classes or brace expansion; `[`, `{` and friends are literal.
Directories must be written as `dir/**`, never as `dir/`.
"""
import re


def has_wildcard(glob):
    return "*" in glob or "?" in glob


def to_regex(glob):
    out = []
    i = 0
    while i < len(glob):
        c = glob[i]
        if c == "*":
            if glob.startswith("**/", i):
                out.append("(?:.*/)?")
                i += 3
            elif glob.startswith("**", i):
                out.append(".*")
                i += 2
            else:
                out.append("[^/]*")
                i += 1
        elif c == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(c))
            i += 1
    return re.compile("^" + "".join(out) + "$")


def matches(glob, path):
    return to_regex(glob).match(path) is not None


def literal_prefix(glob):
    """Leading path segments that contain no wildcard."""
    segments = []
    for segment in glob.split("/"):
        if has_wildcard(segment):
            break
        segments.append(segment)
    return segments


def overlaps(a, b):
    """True if two globs may match a common path. Conservative: undecidable -> True."""
    wild_a, wild_b = has_wildcard(a), has_wildcard(b)
    if not wild_a and not wild_b:
        return a == b
    if not wild_a:
        return matches(b, a)
    if not wild_b:
        return matches(a, b)
    prefix_a, prefix_b = literal_prefix(a), literal_prefix(b)
    n = min(len(prefix_a), len(prefix_b))
    return prefix_a[:n] == prefix_b[:n]


def covers(outer, inner):
    """True if every path `inner` can match is also matched by `outer` (conservative)."""
    if outer == inner:
        return True
    if "**" in inner and "**" not in outer:
        return False
    return matches(outer, inner)
