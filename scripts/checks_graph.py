"""Structure checks: references, cycles, wave layout, widths, step coverage, feature drift."""
from collections import Counter

from findings import Finding


def _phase_map(project):
    return {p.id: p for p in project.plan.phases}


def check_refs(project):
    findings = []
    phases = project.plan.phases
    ids = Counter(p.id for p in phases)
    for pid, count in ids.items():
        if count > 1:
            findings.append(Finding("dup-id", f"phase id {pid} is defined {count} times"))
    by_id = _phase_map(project)
    for phase in phases:
        spec = project.specs.get(phase.spec)
        if spec is None:
            findings.append(Finding("dep-unresolved", f"phase {phase.id} references unknown spec {phase.spec}"))
        else:
            for step in phase.steps:
                if step not in spec.steps:
                    findings.append(
                        Finding("step-coverage", f"phase {phase.id} lists step {step}, which spec {spec.id} does not declare")
                    )
        for dep in phase.depends_on:
            if dep not in by_id:
                findings.append(Finding("dep-unresolved", f"phase {phase.id} depends on unknown phase {dep}"))
    for spec in project.specs.values():
        for dep in spec.depends_on:
            if dep not in project.specs:
                findings.append(Finding("dep-unresolved", f"spec {spec.id} depends on unknown spec {dep}"))
    for wave in project.plan.waves:
        for pid in wave.phases:
            if pid not in by_id:
                findings.append(Finding("dep-unresolved", f"wave {wave.number} lists unknown phase {pid}"))
    return findings


def _find_cycle(graph):
    white, grey, black = 0, 1, 2
    color = {node: white for node in graph}
    stack = []

    def visit(node):
        color[node] = grey
        stack.append(node)
        for nxt in graph.get(node, []):
            if nxt not in color:
                continue
            if color[nxt] == grey:
                return stack[stack.index(nxt) :] + [nxt]
            if color[nxt] == white:
                found = visit(nxt)
                if found:
                    return found
        stack.pop()
        color[node] = black
        return None

    for node in list(graph):
        if color[node] == white:
            found = visit(node)
            if found:
                return found
    return None


def check_cycles(project):
    findings = []
    feature_graph = {s.id: list(s.depends_on) for s in project.specs.values()}
    phase_graph = {p.id: list(p.depends_on) for p in project.plan.phases}
    for label, graph in (("feature", feature_graph), ("phase", phase_graph)):
        cycle = _find_cycle(graph)
        if cycle:
            findings.append(Finding("dep-cycle", f"{label} dependency cycle: {' -> '.join(cycle)}"))
    return findings


def _wave_of(project):
    mapping = {}
    for wave in project.plan.waves:
        for pid in wave.phases:
            mapping.setdefault(pid, wave.number)
    return mapping


def check_waves(project):
    findings = []
    waves = project.plan.waves
    numbers = [w.number for w in waves]
    if sorted(numbers) != list(range(1, len(waves) + 1)):
        findings.append(Finding("wave-numbering", f"waves must be numbered 1..{len(waves)} without gaps or repeats, got {sorted(numbers)}"))

    for wave in waves:
        if not wave.phases:
            findings.append(Finding("wave-empty", f"wave {wave.number} has no phases"))

    seen = Counter(pid for w in waves for pid in w.phases)
    for phase in project.plan.phases:
        if seen[phase.id] == 0:
            findings.append(Finding("wave-coverage", f"phase {phase.id} is not in any wave"))
        elif seen[phase.id] > 1:
            findings.append(Finding("wave-coverage", f"phase {phase.id} is in {seen[phase.id]} waves"))

    wave_of = _wave_of(project)
    by_id = _phase_map(project)
    for phase in project.plan.phases:
        mine = wave_of.get(phase.id)
        if mine is None:
            continue
        for dep in phase.depends_on:
            theirs = wave_of.get(dep)
            if theirs is not None and theirs >= mine:
                findings.append(
                    Finding("wave-order", f"phase {phase.id} (wave {mine}) depends on {dep} (wave {theirs}); a prerequisite must be in an earlier wave")
                )
        spec = project.specs.get(phase.spec)
        for dep in phase.depends_on:
            dep_phase = by_id.get(dep)
            if spec and dep_phase and dep_phase.spec != phase.spec and dep_phase.spec not in spec.depends_on:
                findings.append(
                    Finding("drift-feature-dep", f"phase {phase.id} depends on {dep} (spec {dep_phase.spec}) but spec {spec.id} does not list {dep_phase.spec} in depends_on")
                )

    for spec in project.specs.values():
        mine = [wave_of[p.id] for p in project.plan.phases if p.spec == spec.id and p.id in wave_of]
        for dep_id in spec.depends_on:
            theirs = [wave_of[p.id] for p in project.plan.phases if p.spec == dep_id and p.id in wave_of]
            if mine and theirs and min(mine) <= max(theirs):
                findings.append(
                    Finding("feature-order", f"spec {spec.id} depends on {dep_id}, so all of {dep_id}'s phases (last in wave {max(theirs)}) must finish before {spec.id}'s first phase (wave {min(mine)})")
                )
    return findings


def check_width(project):
    limit = project.plan.header.max_wave_width
    return [
        Finding("wave-width", f"wave {w.number} has {len(w.phases)} phases; max_wave_width is {limit}")
        for w in project.plan.waves
        if len(w.phases) > limit
    ]


def check_step_coverage(project):
    findings = []
    covered = Counter()
    for phase in project.plan.phases:
        for step in phase.steps:
            covered[(phase.spec, step)] += 1
    for spec in project.specs.values():
        for step in spec.steps:
            count = covered[(spec.id, step)]
            if count == 0:
                findings.append(Finding("step-coverage", f"step {step} of spec {spec.id} is not in any phase"))
            elif count > 1:
                findings.append(Finding("step-coverage", f"step {step} of spec {spec.id} is in {count} phases"))
    return findings
