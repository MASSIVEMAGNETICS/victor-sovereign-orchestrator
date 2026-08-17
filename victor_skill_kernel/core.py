from __future__ import annotations

import json
import math
import re
import sqlite3
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable, Sequence

_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9_-]+", re.I)
_STOPWORDS = {
    "the","and","for","with","that","this","from","into","when","must","will","your","you",
    "are","not","use","using","all","any","its","their","then","than","can","should","skill",
    "skills","victor","a","an","of","to","in","on","or","as","by","be","is","it","at",
}
_AUTHORITY_MARKERS = {
    "sovereign", "kernel", "prime", "genesis", "god", "tier", "meta", "always", "never",
    "immutable", "supreme", "mandatory", "must", "authority", "constitutional",
}
_EXECUTION_CLAIM_PATTERNS = [
    re.compile(r"\bimplemented\b", re.I),
    re.compile(r"\bhas been written\b", re.I),
    re.compile(r"\bhas been persisted\b", re.I),
    re.compile(r"\bcompleted\b", re.I),
]


def _tokens(text: str) -> set[str]:
    return {t.lower() for t in _TOKEN_RE.findall(text) if t.lower() not in _STOPWORDS and len(t) > 2}


def _parse_list(value: str) -> tuple[str, ...]:
    value = value.strip()
    if not value:
        return ()
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return ()
        return tuple(x.strip().strip("'\"") for x in inner.split(",") if x.strip())
    return tuple(x.strip() for x in value.split(",") if x.strip())


def _parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end < 0:
        return {}, text
    raw = text[4:end]
    body = text[end + 5 :]
    out: dict[str, str] = {}
    for line in raw.splitlines():
        if not line.strip() or line.lstrip().startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        out[key.strip()] = value.strip().strip("'\"")
    return out, body


@dataclass(frozen=True)
class Skill:
    name: str
    description: str
    path: str
    body: str
    capabilities: tuple[str, ...] = ()
    jurisdiction: str = "unspecified"
    authority: str = "specialist"
    priority: int = 50
    modes: tuple[str, ...] = ()
    depends_on: tuple[str, ...] = ()
    conflicts_with: tuple[str, ...] = ()
    status: str = "active"
    version: str = "0.0.0"

    @property
    def text(self) -> str:
        return " ".join((self.name, self.description, self.jurisdiction, " ".join(self.capabilities), self.body))

    @property
    def token_set(self) -> set[str]:
        return _tokens(self.text)

    @classmethod
    def from_file(cls, path: Path) -> "Skill":
        text = path.read_text(encoding="utf-8")
        fm, body = _parse_frontmatter(text)
        name = fm.get("name", path.parent.name)
        description = fm.get("description", "")
        try:
            priority = int(fm.get("priority", "50"))
        except ValueError:
            priority = 50
        return cls(
            name=name,
            description=description,
            path=str(path),
            body=body,
            capabilities=_parse_list(fm.get("capabilities", "")),
            jurisdiction=fm.get("jurisdiction", "unspecified"),
            authority=fm.get("authority", "specialist"),
            priority=priority,
            modes=_parse_list(fm.get("modes", "")),
            depends_on=_parse_list(fm.get("depends_on", "")),
            conflicts_with=_parse_list(fm.get("conflicts_with", "")),
            status=fm.get("status", "active"),
            version=fm.get("version", "0.0.0"),
        )


@dataclass(frozen=True)
class AuditFinding:
    severity: str
    skill: str
    code: str
    message: str


@dataclass(frozen=True)
class PairOverlap:
    a: str
    b: str
    lexical: float
    capability: float
    jurisdiction: float
    score: float
    recommendation: str


@dataclass
class AuditReport:
    skills: list[dict]
    findings: list[AuditFinding]
    overlaps: list[PairOverlap]
    merge_groups: list[list[str]]
    scores: dict[str, float]

    def to_dict(self) -> dict:
        return {
            "skills": self.skills,
            "findings": [asdict(x) for x in self.findings],
            "overlaps": [asdict(x) for x in self.overlaps],
            "merge_groups": self.merge_groups,
            "scores": self.scores,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True)

    def to_markdown(self) -> str:
        lines = [
            "# Victor Skill Audit", "", f"Skills scanned: **{len(self.skills)}**",
            f"Findings: **{len(self.findings)}**", f"Merge groups: **{len(self.merge_groups)}**", "",
            "## Scores", "", "| Skill | Score |", "|---|---:|",
        ]
        for name, score in sorted(self.scores.items(), key=lambda x: (-x[1], x[0])):
            lines.append(f"| `{name}` | {score:.1f}/10 |")
        lines.extend(["", "## Findings", ""])
        if not self.findings:
            lines.append("No findings.")
        else:
            for f in self.findings:
                lines.append(f"- **{f.severity.upper()}** `{f.skill}` `{f.code}` — {f.message}")
        lines.extend(["", "## Highest Overlaps", "", "| A | B | Score | Recommendation |", "|---|---|---:|---|"])
        for p in sorted(self.overlaps, key=lambda x: -x.score)[:20]:
            lines.append(f"| `{p.a}` | `{p.b}` | {p.score:.3f} | {p.recommendation} |")
        lines.extend(["", "## Merge Groups", ""])
        if not self.merge_groups:
            lines.append("No merge groups crossed the threshold.")
        else:
            for g in self.merge_groups:
                lines.append("- " + " + ".join(f"`{x}`" for x in g))
        return "\n".join(lines) + "\n"


def load_skills(root: str | Path) -> list[Skill]:
    root = Path(root)
    files = [root] if root.is_file() else sorted(root.rglob("SKILL.md"))
    skills: list[Skill] = []
    for path in files:
        try:
            skills.append(Skill.from_file(path))
        except (OSError, UnicodeError) as exc:
            raise RuntimeError(f"Failed to load {path}: {exc}") from exc
    return skills


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    union = a | b
    return len(a & b) / len(union) if union else 0.0


def _pair_overlap(a: Skill, b: Skill) -> PairOverlap:
    lexical = _jaccard(a.token_set, b.token_set)
    capability = _jaccard(set(map(str.lower, a.capabilities)), set(map(str.lower, b.capabilities)))
    jurisdiction = 1.0 if a.jurisdiction != "unspecified" and a.jurisdiction == b.jurisdiction else 0.0
    score = 0.45 * lexical + 0.40 * capability + 0.15 * jurisdiction
    if score >= 0.52:
        recommendation = "merge-or-split-jurisdiction"
    elif score >= 0.36:
        recommendation = "review-overlap"
    else:
        recommendation = "keep-distinct"
    return PairOverlap(a.name, b.name, lexical, capability, jurisdiction, score, recommendation)


def _connected_groups(skills: Sequence[Skill], overlaps: Sequence[PairOverlap], threshold: float = 0.52) -> list[list[str]]:
    names = {s.name for s in skills}
    graph = {n: set() for n in names}
    for p in overlaps:
        if p.score >= threshold:
            graph[p.a].add(p.b)
            graph[p.b].add(p.a)
    seen: set[str] = set()
    groups: list[list[str]] = []
    for n in sorted(names):
        if n in seen or not graph[n]:
            continue
        stack = [n]
        comp: list[str] = []
        while stack:
            cur = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            comp.append(cur)
            stack.extend(sorted(graph[cur] - seen))
        if len(comp) > 1:
            groups.append(sorted(comp))
    return groups


def audit_skills(skills: Sequence[Skill]) -> AuditReport:
    findings: list[AuditFinding] = []
    seen_names: dict[str, int] = {}
    for s in skills:
        seen_names[s.name] = seen_names.get(s.name, 0) + 1
        if not s.description:
            findings.append(AuditFinding("high", s.name, "missing-description", "No description/frontmatter routing hint."))
        if s.jurisdiction == "unspecified":
            findings.append(AuditFinding("medium", s.name, "missing-jurisdiction", "Jurisdiction is unspecified; routing can become ambiguous."))
        if not s.capabilities:
            findings.append(AuditFinding("medium", s.name, "missing-capabilities", "No explicit capability list."))
        authority_hits = sorted(_AUTHORITY_MARKERS & _tokens(f"{s.name} {s.description} {s.body}"))
        if len(authority_hits) >= 4 and s.authority not in {"constitution", "governance"}:
            findings.append(AuditFinding("medium", s.name, "authority-inflation", f"Many authority markers ({', '.join(authority_hits[:8])}) without constitutional jurisdiction."))
        if any(p.search(s.body) for p in _EXECUTION_CLAIM_PATTERNS) and "evidence" not in s.body.lower() and "receipt" not in s.body.lower():
            findings.append(AuditFinding("high", s.name, "unverified-execution-claim", "Contains completion/implementation language without an explicit evidence or receipt requirement."))
        if s.status.lower() not in {"draft", "generated", "validated", "tested", "trusted", "active", "deprecated", "retired"}:
            findings.append(AuditFinding("low", s.name, "unknown-status", f"Unknown lifecycle status: {s.status}"))

    for name, count in seen_names.items():
        if count > 1:
            findings.append(AuditFinding("high", name, "duplicate-name", f"Skill name appears {count} times."))

    overlaps: list[PairOverlap] = []
    for i, a in enumerate(skills):
        for b in skills[i + 1 :]:
            overlaps.append(_pair_overlap(a, b))

    groups = _connected_groups(skills, overlaps)
    severity_penalty = {"high": 1.4, "medium": 0.7, "low": 0.3}
    scores: dict[str, float] = {}
    for s in skills:
        penalty = sum(severity_penalty.get(f.severity, 0.5) for f in findings if f.skill == s.name)
        bonus = (0.4 if s.capabilities else 0.0) + (0.4 if s.jurisdiction != "unspecified" else 0.0)
        bonus += 0.3 if s.depends_on or s.authority in {"constitution", "governance"} else 0.0
        scores[s.name] = max(0.0, min(10.0, 8.4 + bonus - penalty))

    return AuditReport(
        skills=[{k: v for k, v in asdict(s).items() if k != "body"} for s in skills],
        findings=findings,
        overlaps=overlaps,
        merge_groups=groups,
        scores=scores,
    )


def route_skill(query: str, skills: Sequence[Skill], top_k: int = 5) -> list[tuple[Skill, float]]:
    q = _tokens(query)
    if not q:
        return []
    ranked: list[tuple[Skill, float]] = []
    for s in skills:
        if s.status.lower() in {"deprecated", "retired"}:
            continue
        name_tokens = _tokens(s.name)
        desc_tokens = _tokens(s.description)
        cap_tokens = _tokens(" ".join(s.capabilities))
        jurisdiction_tokens = _tokens(s.jurisdiction)
        body_tokens = _tokens(s.body)
        score = (
            3.0 * len(q & cap_tokens) + 2.5 * len(q & jurisdiction_tokens) + 2.0 * len(q & name_tokens)
            + 1.4 * len(q & desc_tokens) + 0.35 * len(q & body_tokens) + s.priority / 100.0
        )
        denominator = 1.0 + math.log2(2 + len(s.token_set)) / 20.0
        ranked.append((s, score / denominator))
    ranked.sort(key=lambda x: (-x[1], -x[0].priority, x[0].name))
    return ranked[:top_k]


class SkillRegistry:
    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self.conn.executescript(
            """
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS skills (
                name TEXT PRIMARY KEY,
                version TEXT NOT NULL,
                jurisdiction TEXT NOT NULL,
                authority TEXT NOT NULL,
                priority INTEGER NOT NULL,
                status TEXT NOT NULL,
                description TEXT NOT NULL,
                path TEXT NOT NULL,
                capabilities_json TEXT NOT NULL,
                modes_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS edges (
                source TEXT NOT NULL,
                relation TEXT NOT NULL,
                target TEXT NOT NULL,
                UNIQUE(source, relation, target)
            );
            CREATE TABLE IF NOT EXISTS receipts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill TEXT NOT NULL,
                action TEXT NOT NULL,
                evidence TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        self.conn.commit()

    def register(self, skill: Skill) -> None:
        self.conn.execute(
            """INSERT INTO skills(name,version,jurisdiction,authority,priority,status,description,path,capabilities_json,modes_json)
               VALUES(?,?,?,?,?,?,?,?,?,?)
               ON CONFLICT(name) DO UPDATE SET
                 version=excluded.version, jurisdiction=excluded.jurisdiction, authority=excluded.authority,
                 priority=excluded.priority, status=excluded.status, description=excluded.description,
                 path=excluded.path, capabilities_json=excluded.capabilities_json, modes_json=excluded.modes_json""",
            (
                skill.name, skill.version, skill.jurisdiction, skill.authority, skill.priority, skill.status,
                skill.description, skill.path, json.dumps(skill.capabilities), json.dumps(skill.modes),
            ),
        )
        self.conn.execute("DELETE FROM edges WHERE source=?", (skill.name,))
        for dep in skill.depends_on:
            self.conn.execute("INSERT OR IGNORE INTO edges(source,relation,target) VALUES(?,?,?)", (skill.name, "depends_on", dep))
        for conflict in skill.conflicts_with:
            self.conn.execute("INSERT OR IGNORE INTO edges(source,relation,target) VALUES(?,?,?)", (skill.name, "conflicts_with", conflict))
        self.conn.commit()

    def register_many(self, skills: Iterable[Skill]) -> None:
        for s in skills:
            self.register(s)

    def receipt(self, skill: str, action: str, evidence: str) -> int:
        if not evidence.strip():
            raise ValueError("Evidence is required; creation/completion never implies trust.")
        cur = self.conn.execute("INSERT INTO receipts(skill,action,evidence) VALUES(?,?,?)", (skill, action, evidence))
        self.conn.commit()
        return int(cur.lastrowid)

    def graph(self) -> dict:
        skills = [dict(r) for r in self.conn.execute("SELECT * FROM skills ORDER BY priority DESC, name")]
        edges = [dict(r) for r in self.conn.execute("SELECT * FROM edges ORDER BY source, relation, target")]
        return {"skills": skills, "edges": edges}

    def close(self) -> None:
        self.conn.close()
