"""Read-only structural validation of the repository agent toolkit."""
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit

try:
    import yaml
except ImportError:
    print("BLOCKED: PyYAML is required; see requirements.txt", file=sys.stderr)
    raise SystemExit(2)

ROOT = Path(__file__).resolve().parents[2]
BASELINE = set("build investigate research verify review fix release deploy publish push pull".split())
CONTRACTS = "core authorization verification git-github deployment handoff memory scopes".split()
ADAPTERS = (".agents", ".claude")
ERRORS = []


class UniqueLoader(yaml.SafeLoader):
    """Reject ambiguous metadata instead of silently keeping the last key."""


def unique_mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise ValueError(f"Duplicate YAML key: {key}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def check(condition, message):
    if not condition:
        ERRORS.append(message)


def read(path):
    target = ROOT / path
    check(target.is_file(), f"Missing file: {path}")
    return target.read_text() if target.is_file() else ""


def parse(text, label):
    try:
        value = yaml.load(text, Loader=UniqueLoader)
        if not isinstance(value, dict):
            raise ValueError("Expected a mapping")
        return value
    except (yaml.YAMLError, ValueError, TypeError) as exc:
        ERRORS.append(f"{label}: {exc}")
        return {}


def frontmatter(path):
    text = read(path)
    match = re.match(r"\A---\n(.*?)\n---\n", text, re.S)
    check(match is not None, f"Missing frontmatter: {path}")
    return parse(match[1], str(path)) if match else {}, text


def main():
    required = ["AGENTS.md", "CLAUDE.md", ".agent/README.md", ".agent/project.yaml",
                ".agent/integrations/README.md", ".agent/workflows/README.md",
                ".agent/hooks/README.md", ".agent/evals/skill-routing.md"]
    required += [f".agent/contracts/{name}.md" for name in CONTRACTS]
    for path in required:
        check((ROOT / path).is_file(), f"Missing baseline surface: {path}")
    project = parse(read(".agent/project.yaml"), "project.yaml")
    check(project.get("schema_version") == 1, "Unsupported schema version")
    identity = project.get("project", {})
    repo = project.get("repository", {})
    check(identity.get("id") == "github:jikovec/bank2excel-finance", "Unexpected project identity")
    check(identity.get("type") == "application", "Expected application project type")
    check(repo == dict(host="github", owner="jikovec", name="bank2excel-finance",
                       default_branch="main", canonical_remote="origin"), "Repository binding mismatch")
    check(project.get("organization") == {"id": None, "name": None}, "Unexpected organization binding")
    check(project.get("ownership") == {"class": "user-owned"}, "Unexpected ownership classification")
    check(project.get("mind_seed") == {"enabled": False, "binding": None}, "Unreviewed Mind-Seed binding")
    check(not (ROOT / ".mind-seed").exists(), "Mind-Seed activation requires binding reconciliation")
    expected_keys = {"schema_version", "project", "repository", "organization", "ownership",
                     "agent", "environment", "integrations", "workflows", "mind_seed"}
    check(set(project) == expected_keys, "Unexpected/missing metadata keys; review stable schema changes")
    try:
        remote = subprocess.check_output(["git", "remote", "get-url", "origin"], cwd=ROOT, text=True).strip()
        check(remote in {"https://github.com/jikovec/bank2excel-finance.git",
                         "https://github.com/jikovec/bank2excel-finance",
                         "git@github.com:jikovec/bank2excel-finance.git"}, "Origin identity differs from metadata")
    except subprocess.CalledProcessError:
        ERRORS.append("Cannot read origin remote")
    for path in project.get("environment", {}).get("source_files", []):
        check((ROOT / path).is_file(), f"Missing environment source: {path}")
    check(project.get("agent") == {"instructions": "AGENTS.md", "canonical_skills": "skills/",
                                  "project_specific_skills": "skills/project/"}, "Agent discovery mismatch")
    for section in ("integrations", "workflows"):
        check(project.get(section) == {"directory": f".agent/{section}/"}, f"Invalid {section} binding")

    canonical = sorted((ROOT / "skills").glob("*/SKILL.md"))
    check({p.parent.name for p in canonical} == BASELINE, "Baseline skill set mismatch")
    project_skills = sorted((ROOT / "skills/project").glob("*/SKILL.md"))
    all_skills = canonical + project_skills
    names = [p.parent.name for p in all_skills]
    check(len(names) == len(set(names)), "Colliding project/baseline skill names")
    descriptions = []
    routing = read(".agent/evals/skill-routing.md")
    for path in all_skills:
        rel = path.relative_to(ROOT)
        name = path.parent.name
        fm, _ = frontmatter(rel)
        check(set(fm) == {"name", "description"}, f"Nonportable frontmatter: {rel}")
        check(fm.get("name") == name and re.fullmatch(r"[a-z0-9-]+", name), f"Invalid skill name: {rel}")
        desc = fm.get("description")
        check(isinstance(desc, str) and bool(desc.strip()), f"Missing description: {rel}")
        descriptions.append(desc)
        for provider in ADAPTERS:
            adapter = Path(provider) / "skills" / name / "SKILL.md"
            afm, body = frontmatter(adapter)
            check(afm == fm, f"Adapter metadata drift: {adapter}")
            expected = (f"---\nname: {name}\ndescription: {desc}\n---\n\n"
                        f"Read and follow [the canonical workflow](../../../{rel.as_posix()})\n"
                        f"before acting. Resolve `{rel.as_posix()}` from the repository root.\n"
                        "Also follow `AGENTS.md` and applicable scoped repository instructions.\n"
                        "This file exists only for native discovery; do not redefine the workflow here.\n")
            check(body == expected, f"Adapter body drift: {adapter}")
        cases = re.search(rf"^## {re.escape(name)}\n(.*?)(?=^## |\Z)", routing, re.M | re.S)
        check(cases is not None, f"Missing routing section: {name}")
        if cases:
            check(cases[1].count("- Positive:") >= 3 and cases[1].count("- Negative:") >= 2,
                  f"Insufficient routing coverage: {name}")
    check(len(descriptions) == len(set(descriptions)), "Duplicate skill descriptions")
    for provider in ADAPTERS:
        found = {p.parent.name for p in (ROOT / provider / "skills").glob("*/SKILL.md")}
        check(found == set(names), f"Unmatched provider adapters: {provider}")
    check(not list((ROOT / ".codex/skills").glob("*/SKILL.md")), "Duplicate Codex discovery surfaces")
    check((ROOT / ".codex/skills/README.md").is_file(), "Missing Codex compatibility pointer")
    check(read("CLAUDE.md").startswith("@AGENTS.md\n"), "Missing Claude policy import")

    docs = [ROOT / "AGENTS.md", ROOT / "CLAUDE.md"]
    for folder in (".agent", "skills", *ADAPTERS):
        docs.extend((ROOT / folder).rglob("*.md"))
    for path in docs:
        for link in re.findall(r"\]\(([^)]+)\)", path.read_text()):
            target = unquote(link.split("#", 1)[0])
            if not target or urlsplit(target).scheme:
                continue
            resolved = (path.parent / target).resolve()
            check(resolved.is_relative_to(ROOT), f"Link escapes repository: {path.relative_to(ROOT)} -> {target}")
            check(resolved.exists(), f"Broken link: {path.relative_to(ROOT)} -> {target}")
    for error in ERRORS:
        print(f"FAIL: {error}", file=sys.stderr)
    if ERRORS:
        return 1
    print(f"PASS: metadata, {len(all_skills)} canonical skills, {len(all_skills)*len(ADAPTERS)} adapters, "
          f"{len(all_skills)*5} minimum routing cases, and toolkit links")
    print("Structural evidence only; review semantics and test native discovery separately.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
