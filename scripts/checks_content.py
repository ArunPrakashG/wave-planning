"""Content checks: ownership, acceptance criteria, model routing."""
from itertools import combinations

from findings import Finding
from globs import covers, overlaps
from routing import MODELS, NeedsPlanningError, derive_model

VERIFY_PREFIXES = ("test:", "cmd:", "http:", "design-fidelity:")


def check_ownership(project):
    findings = []
    for spec in project.specs.values():
        for glob in spec.owns:
            if "{" in glob or "}" in glob:
                findings.append(Finding("owns-glob", f"spec {spec.id} owns {glob!r}; braces are not supported, list each path separately"))
    phases = {p.id: p for p in project.plan.phases}
    for phase in project.plan.phases:
        spec = project.specs.get(phase.spec)
        if not phase.owns:
            findings.append(Finding("owns-empty", f"phase {phase.id} owns no paths; every phase must own what it writes"))
        for glob in phase.owns:
            if "{" in glob or "}" in glob:
                findings.append(Finding("owns-glob", f"phase {phase.id} owns {glob!r}; braces are not supported, list each path separately"))
                continue
            if not glob or glob.endswith("/"):
                findings.append(Finding("owns-dir", f"phase {phase.id} owns {glob!r}; write directories as 'dir/**'"))
                continue
            if spec and not any(covers(outer, glob) for outer in spec.owns):
                findings.append(Finding("owns-subset", f"phase {phase.id} owns {glob}, which is outside spec {spec.id}'s owns {spec.owns}"))
    for wave in project.plan.waves:
        members = [phases[pid] for pid in wave.phases if pid in phases]
        for a, b in combinations(members, 2):
            for ga in a.owns:
                for gb in b.owns:
                    if overlaps(ga, gb):
                        findings.append(Finding("owns-overlap", f"wave {wave.number}: {a.id} ({ga}) and {b.id} ({gb}) may write the same files"))
        for shared in wave.integration_owned:
            for member in members:
                if any(overlaps(shared, g) for g in member.owns):
                    findings.append(Finding("owns-integration", f"wave {wave.number}: integration-owned {shared} overlaps {member.id}'s owns; workers must not touch it"))
    return findings


def check_criteria(project):
    findings = []
    wave_of = {}
    for wave in project.plan.waves:
        for pid in wave.phases:
            wave_of.setdefault(pid, wave.number)
    known = {}
    for spec in project.specs.values():
        for criterion in spec.criteria:
            known[criterion.id] = spec
            verify = criterion.verify.strip()
            prefix = next((p for p in VERIFY_PREFIXES if verify.startswith(p)), None)
            if prefix is None or not verify[len(prefix) :].strip():
                findings.append(Finding("criteria-verify", f"{criterion.id} needs verify: starting with one of {VERIFY_PREFIXES} followed by something concrete; got {criterion.verify!r}"))

    listed = {}
    for wave in project.plan.waves:
        for cid in wave.criteria:
            listed.setdefault(cid, []).append(wave.number)
    for cid, spec in known.items():
        waves = listed.get(cid, [])
        if not waves:
            findings.append(Finding("criteria-wave", f"{cid} is not assigned to any wave's criteria"))
            continue
        if len(waves) > 1:
            findings.append(Finding("criteria-wave", f"{cid} is assigned to several waves: {waves}"))
        feature_waves = [wave_of[p.id] for p in project.plan.phases if p.spec == spec.id and p.id in wave_of]
        if feature_waves and waves[0] < max(feature_waves):
            findings.append(Finding("criteria-wave", f"{cid} is gated in wave {waves[0]} but spec {spec.id} has phases through wave {max(feature_waves)}"))
    for cid in listed:
        if cid not in known:
            findings.append(Finding("criteria-wave", f"wave criteria list unknown criterion {cid}"))
    return findings


def check_routing(project):
    findings = []
    for phase in project.plan.phases:
        if phase.model not in MODELS:
            findings.append(Finding("model-invalid", f"phase {phase.id} model {phase.model!r} must be one of {MODELS}"))
            continue
        try:
            derived = derive_model(phase.score)
        except NeedsPlanningError as exc:
            findings.append(Finding("needs-planning", f"phase {phase.id}: {exc}"))
            continue
        except ValueError as exc:
            findings.append(Finding("score-invalid", f"phase {phase.id}: {exc}"))
            continue
        if phase.model != derived and not phase.override:
            findings.append(Finding("model-drift", f"phase {phase.id} is {phase.model} but its score derives {derived}; fix the score or add 'override: \"reason\"'"))
        spec = project.specs.get(phase.spec)
        if spec and spec.risk and phase.model != "opus":
            findings.append(Finding("risk-not-opus", f"phase {phase.id} is {phase.model} but spec {spec.id} is risk-flagged {spec.risk}; risk-flagged work runs on opus"))
    return findings
