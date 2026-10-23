#!/usr/bin/env python3
"""Apply Xyberah white-label branding to a Promptfoo source checkout.

Usage: python3 apply-branding.py <promptfoo-src-dir> <branding-assets-dir>

Scope: web UI (logo, favicon, page titles, visible product name) and the CLI
(command name, help text, hints). Functional identifiers are deliberately left
alone so existing configs keep working: provider ids (promptfoo:redteam:*),
PROMPTFOO_* env vars, promptfooconfig.yaml, ~/.promptfoo, npm package imports.
References to the vendor's hosted services ("Promptfoo Cloud/Enterprise") and
the MIT copyright notice are kept, because those still point at Promptfoo, Inc.
"""
import pathlib
import re
import shutil
import sys

BRAND = "Xyberah"
CLI = "xyberah"

src = pathlib.Path(sys.argv[1]).resolve()
assets = pathlib.Path(sys.argv[2]).resolve()

SUBCOMMANDS = (
    "eval|view|init|redteam|share|auth|cache|config|debug|delete|export|generate|"
    "feedback|import|list|logs|scan-model|optimize|retry|validate|show|mcp|code-scans"
)

# (pattern, replacement) applied to every non-test .ts/.tsx under src/
RULES = [
    # CLI invocation hints
    (re.compile(r"npx promptfoo@latest\b"), CLI),
    (re.compile(r"npx promptfoo\b"), CLI),
    (re.compile(r"(?<![\w./@:-])promptfoo (?=(?:%s)\b)" % SUBCOMMANDS), CLI + " "),
    # Lower-case product name in prose (explicit phrases only - lowercase
    # "promptfoo" is also used for functional ids, so no blanket replace)
    (re.compile(r"\bpromptfoo API\b"), f"{BRAND} API"),
    (re.compile(r"\bpromptfoo will\b"), f"{BRAND} will"),
    (re.compile(r"\bpromptfoo is\b"), f"{BRAND} is"),
    (re.compile(r"\binstalling promptfoo\b"), f"installing {BRAND}"),
    (re.compile(r"\binstalled promptfoo\b"), f"installed {BRAND}"),
    (re.compile(r"\| promptfoo\b"), f"| {BRAND}"),
    (re.compile(r"\bpromptfoo \|"), f"{BRAND} |"),
    (re.compile(r"(<h[1-3][^>]*>)promptfoo<"), r"\g<1>" + BRAND + "<"),
    (re.compile(r"\bTells promptfoo\b|\btells promptfoo\b"), f"tells {BRAND}"),
    # Capitalised product name, except vendor services / legal notices / identifiers
    (
        re.compile(
            r"(?<![\w-])Promptfoo(?![\w-])"
            r"(?! (?:Cloud|Enterprise|cloud|Inc)\b)(?!, Inc)(?! is a MIT)(?! is an MIT)"
        ),
        BRAND,
    ),
]

SKIP = re.compile(r"(\.test\.|\.spec\.|__mocks__|\.stories\.|/test/|/tests/)")


def is_code_line_safe(line: str) -> bool:
    # never touch import specifiers
    s = line.lstrip()
    return not (s.startswith("import ") or " from '" in line or 'from "' in line)


changed = 0
for path in list(src.glob("src/**/*.ts")) + list(src.glob("src/**/*.tsx")):
    rel = str(path.relative_to(src))
    if SKIP.search(rel) or "node_modules" in rel:
        continue
    text = path.read_text(encoding="utf-8")
    out_lines = []
    for line in text.splitlines(keepends=True):
        if is_code_line_safe(line):
            for pat, rep in RULES:
                line = pat.sub(rep, line)
        out_lines.append(line)
    new = "".join(out_lines)
    if new != text:
        path.write_text(new, encoding="utf-8")
        changed += 1
print(f"[brand] rewrote strings in {changed} source files")

# --- CLI program name -------------------------------------------------------
main_ts = src / "src/main.ts"
t = main_ts.read_text()
t = t.replace("new Command('promptfoo')", f"new Command('{CLI}')")
main_ts.write_text(t)

# package.json bin: xyberah only
pkg = src / "package.json"
t = pkg.read_text()
t = re.sub(
    r'"bin": \{\s*"promptfoo": "dist/src/entrypoint.js",\s*"pf": "dist/src/entrypoint.js"\s*\}',
    f'"bin": {{\n    "{CLI}": "dist/src/entrypoint.js"\n  }}',
    t,
)
pkg.write_text(t)

# --- Web UI assets ----------------------------------------------------------
app = src / "src/app"
shutil.copy(assets / "logo.svg", app / "src/assets/logo.svg")
for f in ("favicon.ico", "favicon.png", "favicon-16x16.png", "favicon-32x32.png"):
    shutil.copy(assets / f, app / "public" / f)

idx = app / "index.html"
t = idx.read_text()
t = t.replace("<title>promptfoo</title>", f"<title>{BRAND}</title>")
t = t.replace('content="LLM testing and evaluation"', f'content="{BRAND} - LLM testing and evaluation"')
t = re.sub(r'\s*<meta property="og:image"[^>]*/>', "", t)
idx.write_text(t)

# Header logo: icon + XYBERAH wordmark (text keeps theme colour for dark mode)
logo = app / "src/components/Logo.tsx"
t = logo.read_text()
t = t.replace('alt="Promptfoo Logo"', f'alt="{BRAND} Logo"')
t = re.sub(r">\s*promptfoo\s*</span>", f">\n        {BRAND.upper()}\n      </span>", t)
t = t.replace("w-[25px]", "w-[32px]")
t = t.replace("font-semibold", "font-extrabold")
logo.write_text(t)

for p in app.rglob("*.tsx"):
    if SKIP.search(str(p)):
        continue
    s = p.read_text()
    n = s.replace('alt="Promptfoo Logo"', f'alt="{BRAND} Logo"').replace('alt="Promptfoo"', f'alt="{BRAND}"')
    n = n.replace("'promptfoo-eval-history.", "'xyberah-eval-history.")
    if n != s:
        p.write_text(n)

print("[brand] done")
