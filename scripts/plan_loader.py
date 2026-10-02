"""Load a wave-planning project: root plan.md plus docs/waves/specs/*.md.

Machine-readable data lives in fenced blocks tagged with an info string:
  ```yaml header | phase | wave | status   (in plan.md)
  ```yaml criteria                          (in specs)
and in the `---` frontmatter of each spec. Everything else is prose for humans.
"""
import re
from dataclasses import dataclass, field
from pathlib import Path

from miniyaml import MiniYamlError, parse_document

DEFAULT_MAX_WAVE_WIDTH = 8

_FENCE_RE = re.compile(r"^```yaml (\w+)[ \t]*\n(.*?)^```[ \t]*$", re.S | re.M)
_FRONTMATTER_RE = re.compile(r"\A---[ \t]*\n(.*?)^---[ \t]*$", re.S | re.M)


class PlanFormatError(ValueError):
    pass


@dataclass
class Criterion:
    id: str  # global id, e.g. "F2.AC1"
    text: str
    verify: str


@dataclass
class Spec:
    id: str
    title: str
    depends_on: list
    owns: list
    reads: list
    risk: list
    steps: list
    criteria: list
    path: str


@dataclass
class Phase:
    id: str
    spec: str
    steps: list
    owns: list
    depends_on: list
    model: str
    score: dict
    rationale: str
    override: str = None


@dataclass
class Wave:
    number: int
    phases: list
    integration_owned: list
    criteria: list
    integration_checks: list


@dataclass
class Header:
    design: str
    bootstrap: str
    gates: dict
    max_wave_width: int


@dataclass
class Plan:
    header: Header
    phases: list
    waves: list
    path: str


@dataclass
class Project:
    root: Path
    plan: Plan
    specs: dict = field(default_factory=dict)


def _read(path):
    """Read a UTF-8 file with newlines normalised, so CRLF files parse like LF files."""
    return Path(path).read_text(encoding="utf-8").replace("\r\n", "\n").replace("\r", "\n")


def fenced_blocks(text, kind):
    return [body for tag, body in _FENCE_RE.findall(text) if tag == kind]


def _parse(body, where):
    try:
        return parse_document(body)
    except MiniYamlError as exc:
        raise PlanFormatError(f"{where}: {exc}") from exc


def _need(doc, key, where):
    if key not in doc or doc[key] is None:
        raise PlanFormatError(f"{where}: missing required field {key!r}")
    return doc[key]


def _need_str(doc, key, where):
    value = _need(doc, key, where)
    if not isinstance(value, str):
        raise PlanFormatError(f"{where}: {key!r} must be text, got {value!r}")
    return value


def _str_list(doc, key, where, required=True):
    if key not in doc or doc[key] is None:
        if required:
            raise PlanFormatError(f"{where}: missing required field {key!r}")
        return []
    value = doc[key]
    if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
        raise PlanFormatError(f"{where}: {key!r} must be a flow list of text, e.g. [a, b]")
    return value


def parse_spec(path):
    path = Path(path)
    where = str(path)
    text = _read(path)
    match = _FRONTMATTER_RE.match(text)
    if not match:
        raise PlanFormatError(f"{where}: missing '---' frontmatter at the top of the file")
    front = _parse(match.group(1), f"{where} frontmatter")
    spec_id = _need_str(front, "id", where)
    criteria = []
    for body in fenced_blocks(text, "criteria"):
        for key, entry in _parse(body, f"{where} criteria").items():
            label = f"{where} criterion {key}"
            if not isinstance(entry, dict):
                raise PlanFormatError(f"{label}: expected {{text: ..., verify: ...}}")
            criteria.append(
                Criterion(
                    id=f"{spec_id}.{key}",
                    text=_need_str(entry, "text", label),
                    verify=str(entry.get("verify") or ""),
                )
            )
    return Spec(
        id=spec_id,
        title=_need_str(front, "title", where),
        depends_on=_str_list(front, "depends_on", where),
        owns=_str_list(front, "owns", where),
        reads=_str_list(front, "reads", where, required=False),
        risk=_str_list(front, "risk", where, required=False),
        steps=_str_list(front, "steps", where),
        criteria=criteria,
        path=where,
    )


def parse_plan(path):
    path = Path(path)
    where = str(path)
    text = _read(path)

    headers = fenced_blocks(text, "header")
    if len(headers) != 1:
        raise PlanFormatError(f"{where}: expected exactly one ```yaml header block, found {len(headers)}")
    h = _parse(headers[0], f"{where} header")
    gates = h.get("gates") or {}
    if not isinstance(gates, dict):
        raise PlanFormatError(f"{where} header: 'gates' must be a map like {{lint: \"...\"}}")
    width = h.get("max_wave_width", DEFAULT_MAX_WAVE_WIDTH)
    if isinstance(width, bool) or not isinstance(width, int) or width < 1:
        raise PlanFormatError(f"{where} header: 'max_wave_width' must be a positive integer")
    header = Header(design=h.get("design"), bootstrap=h.get("bootstrap"), gates=gates, max_wave_width=width)

    phases = []
    for body in fenced_blocks(text, "phase"):
        p = _parse(body, f"{where} phase")
        pid = _need_str(p, "id", f"{where} phase")
        label = f"{where} phase {pid}"
        score = _need(p, "score", label)
        if not isinstance(score, dict):
            raise PlanFormatError(f"{label}: 'score' must be a map")
        override = p.get("override")
        phases.append(
            Phase(
                id=pid,
                spec=_need_str(p, "spec", label),
                steps=_str_list(p, "steps", label),
                owns=_str_list(p, "owns", label),
                depends_on=_str_list(p, "depends_on", label),
                model=_need_str(p, "model", label),
                score=score,
                rationale=str(p.get("rationale") or ""),
                override=None if override is None else str(override),
            )
        )

    waves = []
    for body in fenced_blocks(text, "wave"):
        w = _parse(body, f"{where} wave")
        number = _need(w, "wave", f"{where} wave")
        if isinstance(number, bool) or not isinstance(number, int):
            raise PlanFormatError(f"{where} wave: 'wave' must be an integer, got {number!r}")
        label = f"{where} wave {number}"
        waves.append(
            Wave(
                number=number,
                phases=_str_list(w, "phases", label),
                integration_owned=_str_list(w, "integration_owned", label, required=False),
                criteria=_str_list(w, "criteria", label, required=False),
                integration_checks=_str_list(w, "integration_checks", label, required=False),
            )
        )
    if not phases:
        raise PlanFormatError(f"{where}: no ```yaml phase blocks found")
    if not waves:
        raise PlanFormatError(f"{where}: no ```yaml wave blocks found")
    return Plan(header=header, phases=phases, waves=waves, path=where)


def load_project(root):
    root = Path(root)
    plan_path = root / "plan.md"
    if not plan_path.is_file():
        raise PlanFormatError(f"{plan_path}: not found (run from the project root or pass --root)")
    specs_dir = root / "docs" / "waves" / "specs"
    paths = sorted(specs_dir.glob("*.md")) if specs_dir.is_dir() else []
    if not paths:
        raise PlanFormatError(f"{specs_dir}: no spec files found")
    specs = {}
    for path in paths:
        spec = parse_spec(path)
        if spec.id in specs:
            raise PlanFormatError(f"{path}: duplicate spec id {spec.id!r}")
        specs[spec.id] = spec
    return Project(root=root, plan=parse_plan(plan_path), specs=specs)
