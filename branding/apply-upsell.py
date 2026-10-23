#!/usr/bin/env python3
"""Replace Promptfoo Enterprise upsells in the web UI.

Usage: python3 apply-upsell.py <promptfoo-src-dir>

Run before apply-branding.py (anchors match upstream text). Changes:
- red-team "community edition" banner -> Xyberah wording and link
- hide Enterprise-only industry suites (Plugins > Domain-Specific Risks)
- hide Enterprise-only strategies (GCG)
- hide Enterprise-only Model Audit tabs (Cloud, GitHub, Registry)
Every edit is anchored on exact upstream text; the build fails if one is missing.
"""
import pathlib
import re
import sys

app = pathlib.Path(sys.argv[1]).resolve() / "src/app/src"
BRAND_URL = "https://xyberah.com"


def patch(rel, edits):
    path = app / rel
    text = path.read_text(encoding="utf-8")
    for anchor, replacement in edits:
        if isinstance(anchor, re.Pattern):
            text, count = anchor.subn(replacement, text)
            ok = count > 0
        else:
            count = text.count(anchor)
            ok = count == 1
            text = text.replace(anchor, replacement)
        if not ok:
            sys.exit(f"[upsell] {rel}: anchor matched {count} times:\n{anchor}")
    path.write_text(text, encoding="utf-8")


patch("components/EnterpriseBanner.tsx", [
    (re.compile(r"You're using the community edition of Promptfoo's red teaming suite\..*?</a>",
                re.S),
     "You're using Xyberah's red teaming suite. For support and advanced capabilities,{' '}\n"
     "          <a\n"
     f'            href="{BRAND_URL}"\n'
     '            target="_blank"\n'
     '            rel="noopener noreferrer"\n'
     '            className="font-bold underline text-primary hover:text-primary/80"\n'
     "          >\n"
     "            contact Xyberah\n"
     "          </a>"),
])

patch("pages/redteam/setup/components/PluginsTab.tsx", [
    ("{VERTICAL_SUITES.map((suite) => (",
     "{VERTICAL_SUITES.filter((suite) => !suite.requiresEnterprise || hasEnterpriseAccess).map((suite) => ("),
    ("      ...CATEGORY_FILTERS,\n    ];\n  }, [recentlyUsedPlugins, selectedPlugins.size]);",
     "      ...CATEGORY_FILTERS.filter(\n"
     "        (filter) =>\n"
     "          filter.key !== 'Domain-Specific Risks' ||\n"
     "          hasEnterpriseAccess ||\n"
     "          VERTICAL_SUITES.some((suite) => !suite.requiresEnterprise),\n"
     "      ),\n"
     "    ];\n"
     "  }, [recentlyUsedPlugins, selectedPlugins.size, hasEnterpriseAccess]);"),
])

patch("pages/redteam/setup/components/Strategies.tsx", [
    ("  (id) => id !== 'default' && id !== 'multilingual',\n",
     "  (id) => id !== 'default' && id !== 'multilingual' && !STRATEGIES_ENTERPRISE_ONLY.has(id),\n"),
])

patch("pages/model-audit/components/PathSelector.tsx", [
    # locked tab triggers
    (re.compile(r"\n\s*<Tooltip>\s*<TooltipTrigger asChild>\s*<TabsTrigger\s+value=\"(?:cloud|github|registry)\".*?</Tooltip>",
                re.S), ""),
    # their placeholder panels
    (re.compile(r"\n\s*<TabsContent value=\"(?:cloud|github|registry)\">.*?</TabsContent>", re.S), ""),
    ("grid-cols-2 gap-1 sm:!h-10 sm:grid-cols-4", "grid-cols-1 gap-1 sm:!h-10 sm:grid-cols-1"),
])

print("[upsell] done")
