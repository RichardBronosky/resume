#!/usr/bin/env python3
"""Build one resume variant as plain JSON Resume from the single source YAML.

    tools/resume-variant.py <variant> [-o out.json] [--source src/....yaml]

Every output (web HTML, paper DOCX/PDF, ATS DOCX, one-offs) is rendered from
the JSON this writes, so the filtering below is the only place that decides
what appears where. See src/variants/README.md for the vocabulary.
"""

import argparse
import copy
import datetime
import json
import os
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SOURCE = os.path.join(ROOT, "src", "bruno.bronosky.resume.yaml")
VARIANTS_DIR = os.path.join(ROOT, "src", "variants")

# Our own keys. Removed from the output so it stays valid JSON Resume.
PRIVATE_KEYS = ("id", "variants", "replaces", "text")
SECTIONS = ("work", "volunteer", "education", "awards", "certificates",
            "publications", "skills", "languages", "interests", "references",
            "projects")


def load_source(path):
    with open(path) as f:
        for doc in yaml.safe_load_all(f):
            if isinstance(doc, dict) and "basics" in doc:
                return doc
    sys.exit(f"{path}: no document with a 'basics' key")


def load_variant(name):
    """Return (config, lineage). lineage is [name, parent, grandparent, ...]."""
    config, lineage = {}, []
    while name:
        if name in lineage:
            sys.exit(f"variant cycle: {' -> '.join(lineage + [name])}")
        path = os.path.join(VARIANTS_DIR, f"{name}.yaml")
        if not os.path.exists(path):
            sys.exit(f"unknown variant '{name}' (no {path})")
        with open(path) as f:
            own = yaml.safe_load(f) or {}
        lineage.append(name)
        config = deep_merge(own, config)  # child wins
        name = own.get("extends")
    config.pop("extends", None)
    return config, lineage


def deep_merge(base, over):
    out = copy.deepcopy(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def included(item, lineage):
    """`variants:` omitted = everywhere. `None` = nowhere (source of truth only).
    Plain names include, `!name` excludes. Names match the variant or anything
    it extends, so a one-off that extends `paper` gets everything paper gets."""
    if not isinstance(item, dict) or "variants" not in item:
        return True
    names = item["variants"]
    if isinstance(names, str):
        names = [names]
    names = ["None" if n is None else str(n) for n in names]
    if "None" in names:
        return False
    if any(n.startswith("!") and n[1:] in lineage for n in names):
        return False
    wanted = [n for n in names if not n.startswith("!")]
    return not wanted or any(n in lineage for n in wanted)


def strip_private(item):
    if isinstance(item, dict):
        return {k: v for k, v in item.items() if k not in PRIVATE_KEYS}
    return item


def bullet_text(b):
    return b["text"] if isinstance(b, dict) else b


def years_ago(entry, today):
    end = str(entry.get("endDate") or "Present")
    if end.lower() == "present":
        return 0.0
    try:
        d = datetime.date.fromisoformat(end[:10] if len(end) >= 10 else f"{end[:4]}-12-31")
    except ValueError:
        return 0.0
    return (today - d).days / 365.25


def highlight_cap(entry, rules, today):
    """rules: [{within_years: 6, max: 8}, ..., {max: 3}], first match wins."""
    if not rules:
        return None
    age = years_ago(entry, today)
    for rule in rules:
        if "within_years" not in rule or age <= rule["within_years"]:
            return rule.get("max")
    return None


def pick_highlights(entry, lineage, rules, promote, today):
    """Source order is priority order. With `promote_own_bullets`, bullets that
    name this exact variant jump the queue before the cap applies."""
    bullets = [b for b in entry.get("highlights", []) if included(b, lineage)]
    if promote:
        def own(b):
            return isinstance(b, dict) and lineage[0] in (b.get("variants") or [])
        bullets = [b for b in bullets if own(b)] + [b for b in bullets if not own(b)]
    cap = highlight_cap(entry, rules, today)
    if cap is not None:
        bullets = bullets[:cap]
    return [bullet_text(b) for b in bullets]


def build(source, config, lineage, today):
    out = copy.deepcopy(source)
    out["basics"] = deep_merge(out["basics"], config.get("basics", {}))

    if "skills" in config:  # a one-off can swap the whole skills list
        out["skills"] = config["skills"]

    rules = (config.get("highlights") or {}).get("max_by_age")
    promote = bool(config.get("promote_own_bullets"))

    for section in SECTIONS:
        items = out.get(section)
        if not isinstance(items, list):
            continue
        kept = [i for i in items if included(i, lineage)]
        # An aggregate entry (e.g. "Various") stands in for the entries it
        # `replaces`, so when it is shown they are not.
        replaced = {r for i in kept if isinstance(i, dict) for r in i.get("replaces", [])}
        kept = [i for i in kept if not (isinstance(i, dict) and i.get("id") in replaced)]
        result = []
        for item in kept:
            if isinstance(item, dict):
                if "highlights" in item:
                    item["highlights"] = pick_highlights(item, lineage, rules, promote, today)
                if "keywords" in item:
                    item["keywords"] = [bullet_text(k) for k in item["keywords"] if included(k, lineage)]
            result.append(strip_private(item))
        out[section] = result

    profiles = out["basics"].get("profiles")
    if isinstance(profiles, list):
        out["basics"]["profiles"] = [strip_private(p) for p in profiles if included(p, lineage)]
    for k in config.get("drop_basics", []):
        out["basics"].pop(k, None)
    return out


def check_ids(source):
    seen = {}
    for section in SECTIONS:
        for i in source.get(section) or []:
            if isinstance(i, dict) and "id" in i:
                if i["id"] in seen:
                    sys.exit(f"duplicate id '{i['id']}' in {section} and {seen[i['id']]}")
                seen[i["id"]] = section
    for section in SECTIONS:
        for i in source.get(section) or []:
            for r in (i.get("replaces") or []) if isinstance(i, dict) else []:
                if r not in seen:
                    sys.exit(f"'{i.get('id')}' replaces unknown id '{r}'")


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("variant")
    p.add_argument("-o", "--output", help="default: stdout")
    p.add_argument("--source", default=DEFAULT_SOURCE)
    p.add_argument("--today", help="YYYY-MM-DD, for reproducible bullet caps")
    a = p.parse_args()

    today = datetime.date.fromisoformat(a.today) if a.today else datetime.date.today()
    source = load_source(a.source)
    check_ids(source)
    config, lineage = load_variant(a.variant)
    data = json.dumps(build(source, config, lineage, today), indent=2, ensure_ascii=False) + "\n"
    if a.output:
        tmp = a.output + ".tmp"
        with open(tmp, "w") as f:
            f.write(data)
        os.replace(tmp, a.output)
    else:
        sys.stdout.write(data)


if __name__ == "__main__":
    main()
