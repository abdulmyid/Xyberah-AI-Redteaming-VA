#!/usr/bin/env python3
"""Extract garak probe prompts into one JSON file per Xyberah plugin.

Usage: python3 extract_garak.py <out-dir>

Runs at image build time with garak installed. For each plugin it loads the
probes garak runs by default (active=True) from the listed modules, plus any
EXTRA probes, and saves their prompts, goal, detector and, where the garak
detector is a plain string/regex check, the triggers needed to grade locally.
"""
import importlib
import importlib.metadata
import inspect
import json
import pathlib
import sys

from garak import _config, _plugins
import garak

_config.load_base_config()

PLUGINS = {
    "garak:dan": ["dan"],
    "garak:tap": ["tap"],
    "garak:suffix": ["suffix"],
    "garak:grandma": ["grandma"],
    "garak:goodside": ["goodside"],
    "garak:promptinject": ["promptinject"],
    "garak:latentinjection": ["latentinjection"],
    "garak:encoding": ["encoding"],
    "garak:lmrc": ["lmrc"],
    "garak:realtoxicityprompts": ["realtoxicityprompts"],
    "garak:malwaregen": ["malwaregen"],
    "garak:misleading": ["misleading"],
    "garak:snowball": ["snowball"],
    "garak:leakreplay": ["leakreplay"],
    "garak:web-injection": ["web_injection"],
    "garak:packagehallucination": ["packagehallucination"],
    "garak:exploitation": ["exploitation"],
}

# Inactive in garak only because of size; worth offering here
EXTRA = {
    "realtoxicityprompts": [
        "RTPFlirtation", "RTPIdentity_Attack", "RTPInsult", "RTPProfanity",
        "RTPSevere_Toxicity", "RTPSexually_Explicit", "RTPThreat",
    ],
}

# garak detectors that are simple string/regex checks -> graded without an LLM
CHECKS = {
    "base.TriggerListDetector": ("contains", None),
    "encoding.DecodeMatch": ("contains", None),
    "promptinject.AttackRogueString": ("contains", None),
    "leakreplay.StartsWith": ("startswith", None),
    "productkey.Win5x5": ("regex", r"([A-Z0-9]{5}-){4}[A-Z0-9]{5}"),
}
# Detectors that use triggers only as context for a model-based check
LLM_DESPITE_TRIGGERS = {"unsafe_content.ToxicCommentModel"}


def probe_classes(module_name):
    mod = importlib.import_module(f"garak.probes.{module_name}")
    extra = set(EXTRA.get(module_name, []))
    for name, cls in inspect.getmembers(mod, inspect.isclass):
        if cls.__module__ != mod.__name__ or name.startswith("_") or name.endswith(("Full", "Mixin")):
            continue
        if getattr(cls, "active", False) is True or name in extra:
            yield name


def as_list(t):
    if t is None:
        return []
    return [str(x) for x in t] if isinstance(t, (list, tuple, set)) else [str(t)]


def extract(module_name, class_name):
    probe = _plugins.load_plugin(f"probes.{module_name}.{class_name}")
    detector = getattr(probe, "primary_detector", None) or getattr(probe, "recommended_detector", None)
    if isinstance(detector, (list, tuple)):
        detector = detector[0]
    check, pattern = CHECKS.get(detector, (None, None))

    triggers = getattr(probe, "triggers", None)
    if detector == "promptinject.AttackRogueString":
        triggers = [p["settings"]["attack_rogue_string"] for p in probe.pi_prompts]

    prompts = []
    for i, text in enumerate(probe.prompts):
        text = getattr(text, "text", text)
        if not isinstance(text, str) or not text.strip():
            continue
        item = {"prompt": text}
        if check in ("contains", "startswith") and triggers and detector not in LLM_DESPITE_TRIGGERS:
            item["triggers"] = as_list(triggers[i])
        prompts.append(item)

    if check in ("contains", "startswith") and not any(p.get("triggers") for p in prompts):
        check = None  # nothing to match against; fall back to LLM grading
    return {
        "probe": f"{module_name}.{class_name}",
        "goal": getattr(probe, "goal", "") or "",
        "detector": detector or "",
        "check": check,
        **({"pattern": pattern} if check == "regex" else {}),
        "prompts": prompts,
    }


def main():
    out = pathlib.Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    failed = []
    for plugin, modules in PLUGINS.items():
        probes = []
        for m in modules:
            for c in probe_classes(m):
                try:
                    p = extract(m, c)
                except Exception as e:  # a single broken probe should not sink the build
                    failed.append(f"{m}.{c}: {type(e).__name__}: {e}")
                    continue
                if p["prompts"]:
                    probes.append(p)
        if not probes:
            sys.exit(f"[garak] no prompts extracted for {plugin}")
        data = {"garakVersion": garak.__version__, "plugin": plugin, "probes": probes}
        (out / f"{plugin.replace(':', '-')}.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        total = sum(len(p["prompts"]) for p in probes)
        print(f"[garak] {plugin}: {len(probes)} probes, {total} prompts")
    for f in failed:
        print(f"[garak] skipped {f}")

    # Apache-2.0: ship garak's licence (and NOTICE, if any) with the extracted prompts
    for f in importlib.metadata.files("garak") or []:
        if f.name.upper().startswith(("LICENSE", "NOTICE")) and ".dist-info" in str(f):
            (out / f"GARAK-{f.name}").write_bytes(f.locate().read_bytes())


main()
