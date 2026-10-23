// Xyberah: Garak probe plugins (copied to src/redteam/constants/garak.ts at build time).
// Prompts come from NVIDIA garak (Apache-2.0), extracted during the image build.

export const GARAK_JAILBREAK_PLUGINS = [
  'garak:dan',
  'garak:tap',
  'garak:suffix',
  'garak:grandma',
  'garak:goodside',
] as const;

export const GARAK_INJECTION_PLUGINS = [
  'garak:promptinject',
  'garak:latentinjection',
  'garak:encoding',
] as const;

export const GARAK_HARMFUL_PLUGINS = [
  'garak:lmrc',
  'garak:realtoxicityprompts',
  'garak:malwaregen',
  'garak:misleading',
  'garak:snowball',
] as const;

export const GARAK_LEAK_CODE_PLUGINS = [
  'garak:leakreplay',
  'garak:web-injection',
  'garak:packagehallucination',
  'garak:exploitation',
] as const;

export const GARAK_PLUGINS = [
  ...GARAK_JAILBREAK_PLUGINS,
  ...GARAK_INJECTION_PLUGINS,
  ...GARAK_HARMFUL_PLUGINS,
  ...GARAK_LEAK_CODE_PLUGINS,
] as const;

export type GarakPlugin = (typeof GARAK_PLUGINS)[number];

export const GARAK_COLLECTIONS = ['garak:all'] as const;

export type GarakCollection = (typeof GARAK_COLLECTIONS)[number];

type GarakMetadataPlugin = GarakCollection | GarakPlugin;

export const GARAK_RISK_CATEGORIES = {
  'Garak: Jailbreaks': [...GARAK_JAILBREAK_PLUGINS],
  'Garak: Prompt Injection': [...GARAK_INJECTION_PLUGINS],
  'Garak: Harmful Content': [...GARAK_HARMFUL_PLUGINS],
  'Garak: Data Leakage & Code': [...GARAK_LEAK_CODE_PLUGINS],
};

export const GARAK_CATEGORY_DESCRIPTIONS = {
  'Garak: Jailbreaks': 'Jailbreak prompts from the garak scanner (DAN, TAP, GCG, role-play).',
  'Garak: Prompt Injection': 'Direct, indirect and encoded prompt injection probes from garak.',
  'Garak: Harmful Content': 'Toxicity, malware, misinformation and harmful-content probes from garak.',
  'Garak: Data Leakage & Code':
    'Training-data replay, markdown exfiltration/XSS, package hallucination and injection probes from garak.',
};

export const GARAK_PLUGIN_DISPLAY_NAMES: Record<GarakMetadataPlugin, string> = {
  'garak:all': 'Garak: All Probes',
  'garak:dan': 'Garak: DAN Jailbreaks',
  'garak:tap': 'Garak: TAP Jailbreaks',
  'garak:suffix': 'Garak: GCG Adversarial Suffix',
  'garak:grandma': 'Garak: Grandma Role-play',
  'garak:goodside': 'Garak: Goodside Attacks',
  'garak:promptinject': 'Garak: PromptInject Hijacking',
  'garak:latentinjection': 'Garak: Latent (Indirect) Injection',
  'garak:encoding': 'Garak: Encoding Injection',
  'garak:lmrc': 'Garak: LM Risk Cards',
  'garak:realtoxicityprompts': 'Garak: RealToxicityPrompts',
  'garak:malwaregen': 'Garak: Malware Generation',
  'garak:misleading': 'Garak: Misleading Claims',
  'garak:snowball': 'Garak: Snowballed Hallucination',
  'garak:leakreplay': 'Garak: Training Data Replay',
  'garak:web-injection': 'Garak: Markdown Exfil & XSS',
  'garak:packagehallucination': 'Garak: Package Hallucination',
  'garak:exploitation': 'Garak: Template & SQL Injection',
};

export const GARAK_PLUGIN_DESCRIPTIONS: Record<GarakMetadataPlugin, string> = {
  'garak:all': 'Runs every garak probe family included in Xyberah',
  'garak:dan': 'Tests resistance to DAN-style jailbreaks, including AutoDAN and in-the-wild variants',
  'garak:tap': 'Tests resistance to cached Tree-of-Attacks-with-Pruning (TAP) jailbreak prompts',
  'garak:suffix': 'Tests resistance to cached GCG adversarial-suffix jailbreaks',
  'garak:grandma': 'Tests whether "act like my grandma" role-play extracts slurs, keys or drug recipes',
  'garak:goodside':
    'Tests invisible Unicode tag injection, threat-based output control and misinformation about a public figure',
  'garak:promptinject': 'Tests goal hijacking with the PromptInject framework rogue strings',
  'garak:latentinjection':
    'Tests instructions hidden in documents, reports, resumes, WHOIS data and translation tasks',
  'garak:encoding':
    'Tests whether payloads hidden in Base64, ROT13, hex, Morse, Braille and other encodings get decoded and emitted',
  'garak:lmrc': 'Tests Language Model Risk Cards: bullying, deadnaming, quack medicine, sexual content, slurs',
  'garak:realtoxicityprompts': 'Tests whether the model continues RealToxicityPrompts prompts with toxic text',
  'garak:malwaregen': 'Tests whether the model writes malware, payloads or AV-evasion code',
  'garak:misleading': 'Tests whether the model refutes false assertions instead of going along with them',
  'garak:snowball': 'Tests whether the model commits to wrong answers on impossible reasoning questions',
  'garak:leakreplay': 'Tests whether the model replays memorised copyrighted or news text',
  'garak:web-injection':
    'Tests for markdown image/link data exfiltration and cross-site scripting payloads in output',
  'garak:packagehallucination': 'Tests whether generated code imports or recommends non-existent packages',
  'garak:exploitation': 'Tests whether the model emits Jinja template or SQL injection payloads',
};

// Metric names; categoryAliases maps plugin ids to these
export const GARAK_PLUGIN_ALIASES: Record<GarakMetadataPlugin, string> = {
  'garak:all': 'GarakAll',
  'garak:dan': 'GarakDAN',
  'garak:tap': 'GarakTAP',
  'garak:suffix': 'GarakSuffix',
  'garak:grandma': 'GarakGrandma',
  'garak:goodside': 'GarakGoodside',
  'garak:promptinject': 'GarakPromptInject',
  'garak:latentinjection': 'GarakLatentInjection',
  'garak:encoding': 'GarakEncoding',
  'garak:lmrc': 'GarakLMRC',
  'garak:realtoxicityprompts': 'GarakRealToxicityPrompts',
  'garak:malwaregen': 'GarakMalwareGen',
  'garak:misleading': 'GarakMisleading',
  'garak:snowball': 'GarakSnowball',
  'garak:leakreplay': 'GarakLeakReplay',
  'garak:web-injection': 'GarakWebInjection',
  'garak:packagehallucination': 'GarakPackageHallucination',
  'garak:exploitation': 'GarakExploitation',
};

// Plain strings so this file has no imports; metadata.ts casts them to Severity
export const GARAK_PLUGIN_SEVERITIES: Record<GarakMetadataPlugin, string> = {
  'garak:all': 'high',
  'garak:dan': 'high',
  'garak:tap': 'high',
  'garak:suffix': 'high',
  'garak:grandma': 'medium',
  'garak:goodside': 'low',
  'garak:promptinject': 'high',
  'garak:latentinjection': 'high',
  'garak:encoding': 'medium',
  'garak:lmrc': 'medium',
  'garak:realtoxicityprompts': 'medium',
  'garak:malwaregen': 'high',
  'garak:misleading': 'low',
  'garak:snowball': 'low',
  'garak:leakreplay': 'medium',
  'garak:web-injection': 'high',
  'garak:packagehallucination': 'medium',
  'garak:exploitation': 'high',
};
