"""Validate a wave-planning project.

Usage: python3 validate_plan.py [--root DIR] [--json]
Exit 0 when the plan is valid, 1 when there are findings or the files cannot be parsed.
"""
import argparse
import json
import sys
from pathlib import Path

from checks_content import check_criteria, check_ownership, check_routing
from checks_graph import check_cycles, check_refs, check_step_coverage, check_waves, check_width
from findings import Finding
from plan_loader import PlanFormatError, load_project

CHECKS = (
    check_refs,
    check_cycles,
    check_waves,
    check_width,
    check_step_coverage,
    check_ownership,
    check_criteria,
    check_routing,
)


def run(root):
    """Return a list of Findings for the project at `root`."""
    try:
        project = load_project(root)
    except PlanFormatError as exc:
        return [Finding("format", str(exc))]
    findings = []
    for check in CHECKS:
        findings.extend(check(project))
    return findings


def main(argv=None, stdout=None):
    out = stdout or sys.stdout
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="project root containing plan.md (default: .)")
    parser.add_argument("--json", action="store_true", help="print findings as JSON")
    args = parser.parse_args(argv)
    findings = run(Path(args.root))
    if args.json:
        print(json.dumps([{"code": f.code, "message": f.message} for f in findings], indent=2), file=out)
    else:
        for finding in findings:
            print(finding, file=out)
        if findings:
            print(f"FAILED: {len(findings)} error(s)", file=out)
        else:
            print("OK: plan is valid", file=out)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
