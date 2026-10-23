#!/usr/bin/env python3
"""Register the garak probe plugins in a Promptfoo source checkout.

Usage: python3 apply-garak.py <promptfoo-src-dir> <garak-dir>

Copies constants.ts / plugin.ts into src/redteam and adds them to the plugin
lists, metadata maps, collections, grader registry and plugin factories.
Every edit is anchored on exact upstream text and the build fails if an anchor
is missing, so a Promptfoo upgrade cannot silently drop the plugins.
"""
import pathlib
import shutil
import sys

src = pathlib.Path(sys.argv[1]).resolve() / "src/redteam"
here = pathlib.Path(sys.argv[2]).resolve()

shutil.copy(here / "constants.ts", src / "constants/garak.ts")
shutil.copy(here / "plugin.ts", src / "plugins/garak.ts")


def patch(rel, edits):
    path = src / rel
    text = path.read_text(encoding="utf-8")
    for anchor, replacement in edits:
        count = text.count(anchor)
        if count != 1:
            sys.exit(f"[garak] {rel}: expected 1 match for anchor, found {count}:\n{anchor}")
        text = text.replace(anchor, replacement)
    path.write_text(text, encoding="utf-8")


patch("constants/plugins.ts", [
    ("import type { CodingAgentPlugin } from './codingAgents';\n",
     "import type { CodingAgentPlugin } from './codingAgents';\n"
     "import { GARAK_COLLECTIONS, GARAK_PLUGINS } from './garak';\n"
     "import type { GarakPlugin } from './garak';\n"),
    ("  ...CODING_AGENT_COLLECTIONS,\n] as const;\nexport type Collection",
     "  ...CODING_AGENT_COLLECTIONS,\n  ...GARAK_COLLECTIONS,\n] as const;\nexport type Collection"),
    ("  'xstest',\n] as const;\ntype AdditionalPlugin",
     "  'xstest',\n  ...GARAK_PLUGINS,\n] as const;\ntype AdditionalPlugin"),
    ("  'xstest',\n] as const;\n\n// Plugins excluded from multi-input",
     "  'xstest',\n  ...GARAK_PLUGINS,\n] as const;\n\n// Plugins excluded from multi-input"),
    ("  | CodingAgentPlugin;\n", "  | CodingAgentPlugin\n  | GarakPlugin;\n"),
])

strategies = src / "constants/strategies.ts"
strategies.write_text("import { GARAK_PLUGINS } from './garak';\n\n" + strategies.read_text(encoding="utf-8"), encoding="utf-8")
patch("constants/strategies.ts", [
    ("  'xstest',\n] as const;\n\nexport const ADDITIONAL_STRATEGIES",
     "  'xstest',\n  ...GARAK_PLUGINS,\n] as const;\n\nexport const ADDITIONAL_STRATEGIES"),
])

patch("constants/metadata.ts", [
    ("import type { CodingAgentCollection, CodingAgentPlugin } from './codingAgents';\n",
     "import type { CodingAgentCollection, CodingAgentPlugin } from './codingAgents';\n"
     "import {\n  GARAK_CATEGORY_DESCRIPTIONS,\n  GARAK_PLUGIN_ALIASES,\n  GARAK_PLUGIN_DESCRIPTIONS,\n"
     "  GARAK_PLUGIN_DISPLAY_NAMES,\n  GARAK_PLUGIN_SEVERITIES,\n  GARAK_RISK_CATEGORIES,\n} from './garak';\n"
     "import type { GarakCollection, GarakPlugin } from './garak';\n"),
    # subCategoryDescriptions
    ("  ...CODING_AGENT_PLUGIN_DESCRIPTIONS,\n};\n\n// These names are displayed",
     "  ...CODING_AGENT_PLUGIN_DESCRIPTIONS,\n  ...GARAK_PLUGIN_DESCRIPTIONS,\n};\n\n// These names are displayed"),
    # displayNameOverrides
    ("  ...CODING_AGENT_PLUGIN_DISPLAY_NAMES,\n};\n",
     "  ...CODING_AGENT_PLUGIN_DISPLAY_NAMES,\n  ...GARAK_PLUGIN_DISPLAY_NAMES,\n};\n"),
    # riskCategorySeverityMap
    ("  ...codingAgentRiskCategorySeverityMap,\n",
     "  ...codingAgentRiskCategorySeverityMap,\n"
     "  ...(GARAK_PLUGIN_SEVERITIES as Record<GarakCollection | GarakPlugin, Severity>),\n"),
    # riskCategories
    ("  'Coding Agent Security': [...CODING_AGENT_PLUGINS],\n",
     "  'Coding Agent Security': [...CODING_AGENT_PLUGINS],\n\n  ...GARAK_RISK_CATEGORIES,\n"),
    ("  Datasets: 'Pre-defined test cases from research datasets.',\n};\n",
     "  Datasets: 'Pre-defined test cases from research datasets.',\n  ...GARAK_CATEGORY_DESCRIPTIONS,\n};\n"),
    # categoryAliases
    ("  ...CODING_AGENT_PLUGIN_ALIASES,\n};\n",
     "  ...CODING_AGENT_PLUGIN_ALIASES,\n  ...GARAK_PLUGIN_ALIASES,\n};\n"),
    # pluginDescriptions
    ("  ...CODING_AGENT_PLUGIN_DESCRIPTIONS,\n};\n\nexport const strategyDescriptions",
     "  ...CODING_AGENT_PLUGIN_DESCRIPTIONS,\n  ...GARAK_PLUGIN_DESCRIPTIONS,\n};\n\nexport const strategyDescriptions"),
])

# garak:all collection expands to every garak plugin
patch("index.ts", [
    ("import { CODING_AGENT_CORE_PLUGINS, CODING_AGENT_PLUGINS } from './constants/codingAgents';\n",
     "import { CODING_AGENT_CORE_PLUGINS, CODING_AGENT_PLUGINS } from './constants/codingAgents';\n"
     "import { GARAK_PLUGINS } from './constants/garak';\n"),
    ("  'coding-agent:all': CODING_AGENT_PLUGINS,\n",
     "  'coding-agent:all': CODING_AGENT_PLUGINS,\n  'garak:all': GARAK_PLUGINS,\n"),
])

validators = src / "../validators/redteam.ts"
validators.write_text(
    "import { GARAK_PLUGINS } from '../redteam/constants/garak';\n" + validators.read_text(encoding="utf-8"),
    encoding="utf-8",
)
patch("../validators/redteam.ts", [
    ("      } else if (id === 'coding-agent:all') {\n"
     "        expandCollection([...CODING_AGENT_PLUGINS], config, numTests, severity);\n      }\n",
     "      } else if (id === 'coding-agent:all') {\n"
     "        expandCollection([...CODING_AGENT_PLUGINS], config, numTests, severity);\n"
     "      } else if (id === 'garak:all') {\n"
     "        expandCollection([...GARAK_PLUGINS], config, numTests, severity);\n      }\n"),
])

patch("graders.ts", [
    ("import { createCodingAgentGraders } from './plugins/codingAgent/graders';\n",
     "import { createCodingAgentGraders } from './plugins/codingAgent/graders';\n"
     "import { createGarakGraders } from './plugins/garak';\n"),
    ("  ...createCodingAgentGraders(),\n};\n",
     "  ...createCodingAgentGraders(),\n  ...createGarakGraders(),\n};\n"),
])

patch("plugins/index.ts", [
    ("import { PlinyPlugin } from './pliny';\n",
     "import { GARAK_PLUGINS } from '../constants/garak';\n"
     "import { GarakProbePlugin } from './garak';\n"
     "import { PlinyPlugin } from './pliny';\n"),
    ("  createPluginFactory(PlinyPlugin, 'pliny'),\n",
     "  createPluginFactory(PlinyPlugin, 'pliny'),\n"
     "  ...GARAK_PLUGINS.map((pluginId) =>\n"
     "    createPluginFactory(\n"
     "      class extends GarakProbePlugin {\n"
     "        constructor(\n"
     "          provider: ApiProvider,\n"
     "          purpose: string,\n"
     "          injectVar: string,\n"
     "          config: PluginConfig,\n"
     "        ) {\n"
     "          super(provider, purpose, injectVar, config, pluginId);\n"
     "        }\n"
     "      },\n"
     "      pluginId,\n"
     "    ),\n"
     "  ),\n"),
])

print("[garak] registered plugins")
