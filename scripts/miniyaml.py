"""Parser for the small YAML subset used in wave-planning documents.

Supported: top-level `key: value` lines, blank lines, `#` comment lines.
Values: flow lists `[a, b]`, flow maps `{k: v}`, quoted strings, integers,
true/false, null, and plain strings. Flow collections may nest.

Not supported: indentation, block lists/maps, inline comments, multi-line values.
In double-quoted strings a backslash makes the next character literal.
In single-quoted strings a doubled quote ('') is a literal quote.
"""
import re


class MiniYamlError(ValueError):
    pass


_KEY_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_.\-]*)\s*:(?:\s+(.*))?$")
_MAP_KEY_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_.\-]*")
_INT_RE = re.compile(r"^-?\d+$")


def parse_document(text):
    """Parse `key: value` lines into a dict."""
    result = {}
    for lineno, raw in enumerate(text.splitlines(), 1):
        line = raw.rstrip()
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if line[0] in " \t":
            raise MiniYamlError(
                f"line {lineno}: indentation is not supported; "
                "write lists and maps in flow style on one line"
            )
        match = _KEY_RE.match(line)
        if not match:
            raise MiniYamlError(f"line {lineno}: expected 'key: value', got {line!r}")
        key, rest = match.group(1), match.group(2)
        if key in result:
            raise MiniYamlError(f"line {lineno}: duplicate key {key!r}")
        result[key] = parse_value(rest or "", lineno)
    return result


def parse_value(text, lineno=0):
    """Parse a single value (the part after `key: `)."""
    flow = _Flow(text.strip(), lineno)
    value = flow.value(top=True)
    flow.skip_ws()
    if flow.i != len(flow.s):
        flow.fail(f"unexpected trailing text {flow.s[flow.i:]!r}")
    return value


def _scalar(text):
    if text in ("", "null", "~"):
        return None
    if text == "true":
        return True
    if text == "false":
        return False
    if _INT_RE.match(text):
        return int(text)
    return text


class _Flow:
    def __init__(self, text, lineno):
        self.s = text
        self.i = 0
        self.lineno = lineno

    def fail(self, message):
        raise MiniYamlError(f"line {self.lineno}: {message}")

    def peek(self):
        return self.s[self.i] if self.i < len(self.s) else ""

    def skip_ws(self):
        while self.peek() == " ":
            self.i += 1

    def value(self, top=False):
        self.skip_ws()
        c = self.peek()
        if c == "":
            return None
        if c == "[":
            return self.sequence()
        if c == "{":
            return self.mapping()
        if c in ("'", '"'):
            return self.quoted()
        return self.plain(top)

    def sequence(self):
        self.i += 1
        items = []
        self.skip_ws()
        if self.peek() == "]":
            self.i += 1
            return items
        while True:
            items.append(self.value())
            self.skip_ws()
            c = self.peek()
            if c == ",":
                self.i += 1
                self.skip_ws()
                if self.peek() == "]":
                    self.i += 1
                    return items
                continue
            if c == "]":
                self.i += 1
                return items
            self.fail("expected ',' or ']' in list")

    def mapping(self):
        self.i += 1
        out = {}
        self.skip_ws()
        if self.peek() == "}":
            self.i += 1
            return out
        while True:
            self.skip_ws()
            match = _MAP_KEY_RE.match(self.s, self.i)
            if not match:
                self.fail("expected a map key")
            key = match.group(0)
            self.i = match.end()
            self.skip_ws()
            if self.peek() != ":":
                self.fail(f"expected ':' after key {key!r}")
            self.i += 1
            if key in out:
                self.fail(f"duplicate key {key!r}")
            out[key] = self.value()
            self.skip_ws()
            c = self.peek()
            if c == ",":
                self.i += 1
                self.skip_ws()
                if self.peek() == "}":
                    self.i += 1
                    return out
                continue
            if c == "}":
                self.i += 1
                return out
            self.fail("expected ',' or '}' in map")

    def quoted(self):
        quote = self.peek()
        self.i += 1
        buf = []
        while self.i < len(self.s):
            c = self.s[self.i]
            if quote == '"' and c == "\\" and self.i + 1 < len(self.s):
                buf.append(self.s[self.i + 1])
                self.i += 2
                continue
            if c == quote:
                if quote == "'" and self.s[self.i + 1 : self.i + 2] == "'":
                    buf.append("'")
                    self.i += 2
                    continue
                self.i += 1
                return "".join(buf)
            buf.append(c)
            self.i += 1
        self.fail("unterminated quoted string")

    def plain(self, top):
        if top:
            text = self.s[self.i :]
            self.i = len(self.s)
        else:
            start = self.i
            while self.peek() not in ("", ",", "]", "}"):
                self.i += 1
            text = self.s[start : self.i]
        text = text.strip()
        if text == "" and not top:
            self.fail("empty value in a list or map; use null or quotes")
        return _scalar(text)
