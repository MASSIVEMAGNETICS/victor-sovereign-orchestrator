from __future__ import annotations

import argparse
from pathlib import Path

from .core import SkillRegistry, audit_skills, load_skills, route_skill


def _cmd_audit(args: argparse.Namespace) -> int:
    skills = load_skills(args.path)
    report = audit_skills(skills)
    print(report.to_markdown())
    if args.json:
        Path(args.json).write_text(report.to_json() + "\n", encoding="utf-8")
    if args.markdown:
        Path(args.markdown).write_text(report.to_markdown(), encoding="utf-8")
    return 1 if args.fail_on_high and any(f.severity == "high" for f in report.findings) else 0


def _cmd_route(args: argparse.Namespace) -> int:
    skills = load_skills(args.path)
    ranked = route_skill(args.query, skills, top_k=args.top)
    if not ranked:
        print("No routing candidates.")
        return 2
    for i, (skill, score) in enumerate(ranked, 1):
        print(f"{i}. {skill.name}\t{score:.3f}\t{skill.jurisdiction}\t{skill.authority}")
    return 0


def _cmd_register(args: argparse.Namespace) -> int:
    skills = load_skills(args.path)
    reg = SkillRegistry(args.db)
    try:
        reg.register_many(skills)
        print(f"registered={len(skills)} db={args.db}")
    finally:
        reg.close()
    return 0


def _cmd_graph(args: argparse.Namespace) -> int:
    import json
    reg = SkillRegistry(args.db)
    try:
        print(json.dumps(reg.graph(), indent=2, sort_keys=True))
    finally:
        reg.close()
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="victor-skills", description="Victor deterministic skill kernel")
    sub = p.add_subparsers(dest="command", required=True)

    a = sub.add_parser("audit", help="Audit SKILL.md files for overlap, authority collisions and metadata gaps")
    a.add_argument("path")
    a.add_argument("--json")
    a.add_argument("--markdown")
    a.add_argument("--fail-on-high", action="store_true")
    a.set_defaults(func=_cmd_audit)

    r = sub.add_parser("route", help="Deterministically rank skills for a task")
    r.add_argument("path")
    r.add_argument("query")
    r.add_argument("--top", type=int, default=5)
    r.set_defaults(func=_cmd_route)

    reg = sub.add_parser("register", help="Register skills and dependencies into SQLite capability graph")
    reg.add_argument("path")
    reg.add_argument("--db", default="victor-skills.db")
    reg.set_defaults(func=_cmd_register)

    g = sub.add_parser("graph", help="Dump the registered capability graph")
    g.add_argument("--db", default="victor-skills.db")
    g.set_defaults(func=_cmd_graph)
    return p


def main() -> int:
    args = build_parser().parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
