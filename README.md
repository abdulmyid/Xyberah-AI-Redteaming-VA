# Xyberah

Xyberah is a self-hosted platform for testing the security and quality of AI applications built on large language models (LLMs), such as chatbots, RAG assistants and AI agents. It runs as a single Docker container with a web UI and a command-line tool.

## What it is for

- **Red teaming.** Attack your AI application before real attackers do: jailbreaks, prompt injection (direct, indirect and encoded), data leakage, harmful or toxic output, and insecure code generation. It includes Promptfoo's red-team plugins and NVIDIA garak's probe library. The result is a report of what failed, grouped by risk category and severity.
- **Evaluation.** Compare prompts and models side by side against your own test cases and assertions, so you can catch quality regressions before a change goes live.
- **Model audit.** Scan model files (pickle, archives, GGUF and more) for malicious code and unsafe deserialisation before you load them.
- **Self-hosted.** Everything runs on your own machine or server, with telemetry and update checks turned off. The only data that leaves is what you send to the model providers you configure.

Under the hood it is the open-source [Promptfoo](https://github.com/promptfoo/promptfoo) 0.124.1 (MIT), rebranded as Xyberah and extended, built as a linux/amd64 container.

**New here? Start with [SETUP.md](SETUP.md).**

<img width="938" height="451" alt="image" src="https://github.com/user-attachments/assets/45230b87-4a19-4a9f-a8c4-2c5d1b550133" />

Left unchanged on purpose, so existing configs keep working: `promptfooconfig.yaml`, `PROMPTFOO_*` env vars, `promptfoo:redteam:*` provider IDs, data folder `~/.promptfoo`. Mentions of "Promptfoo Cloud/Enterprise" stay because those still point to Promptfoo's hosted service. The MIT `LICENSE` is shipped in `/app/LICENSE`, as the licence requires.

## Build and push (on your machine or CI)

Needs Docker with BuildKit, internet access to Docker Hub, GitHub and npm, and about 8 GB of RAM for Docker.

```bash
# local image only
docker build --platform linux/amd64 -t xyberah:0.124.1 -t xyberah:latest .

# build + push to your registry
docker login registry.example.com
./build-and-push.sh registry.example.com/your-namespace
```

Behind a TLS-intercepting corporate proxy, add `--secret id=ca,src=/path/to/ca-bundle.crt` to the build. The CA is only used during the build and is not saved in the image.

## Run

```bash
docker compose up -d                      # UI at http://localhost:3000
docker exec -it xyberah xyberah --help    # CLI inside the container
docker run --rm -v "$PWD:/work" -w /work -e OPENAI_API_KEY xyberah:0.124.1 xyberah eval -c promptfooconfig.yaml
```

## Garak probes

Red-team test cases from [NVIDIA garak](https://github.com/NVIDIA/garak) (Apache-2.0) are built in as 17 plugins, in four groups on the Red Team → Plugins page:

| Group | Plugins |
|---|---|
| Garak: Jailbreaks | `garak:dan`, `garak:tap`, `garak:suffix`, `garak:grandma`, `garak:goodside` |
| Garak: Prompt Injection | `garak:promptinject`, `garak:latentinjection`, `garak:encoding` |
| Garak: Harmful Content | `garak:lmrc`, `garak:realtoxicityprompts`, `garak:malwaregen`, `garak:misleading`, `garak:snowball` |
| Garak: Data Leakage & Code | `garak:leakreplay`, `garak:web-injection`, `garak:packagehallucination`, `garak:exploitation` |

In a config, use them like any other plugin, or `garak:all` for all of them:

```yaml
redteam:
  plugins:
    - id: garak:encoding
      numTests: 20
    - garak:all
```

How it works:

- During the build, garak (`GARAK_VERSION`, default 0.17.0) is installed in a throwaway stage and the prompts of the probes garak runs by default are saved to `/app/garak/*.json` (plus the RealToxicityPrompts categories). garak itself is not in the final image. Its licence is shipped as `/app/garak/GARAK-LICENSE`.
- Each run picks `numTests` prompts per plugin, spread across that plugin's garak probes. Prompts are used as-is: strategies are not applied, the same as Promptfoo's other dataset plugins.
- Grading: probes whose garak detector is a string check (encoding, promptinject, most latentinjection, leakreplay, goodside Tag, lmrc Deadnaming, grandma Windows keys) are graded the same way locally, with no LLM call. The rest are graded by the red-team grading model, using the probe's goal. `garak:packagehallucination` is graded by the LLM rather than against package registries, so treat its results as indicative.
- Live attack probes that need an attacker model (TAP, PAIR, GCG, AutoDAN generation) are not included. The cached prompts garak ships for them are.

To change the garak version: `docker build --build-arg GARAK_VERSION=0.17.1 ...`. The build fails if a garak family yields no prompts.

## Model Audit

The `modelaudit` CLI (`MODELAUDIT_VERSION`, default 0.2.52) is installed in `/opt/modelaudit`, with its own Python 3.12, because Alpine's Python is newer than modelaudit supports. This is the base install: it covers pickle-family files, archives, GGUF and the other formats modelaudit reads without optional extras. Formats that need TensorFlow, PyTorch, ONNX, etc. are not covered.

## Upgrading to a newer Promptfoo release

```bash
PROMPTFOO_VERSION=0.125.0 ./build-and-push.sh registry.example.com/your-namespace
```

`branding/apply-branding.py` rewrites the code using patterns, so it usually works on new releases. `branding/apply-upsell.py` and `garak/apply-garak.py` edit exact upstream lines and stop the build with the file name if a line has changed; update the anchor in the script when that happens. Check the UI and `xyberah --help` after each upgrade.

## Changing the logo

Replace the files in `branding/assets/` (`logo.svg` is the icon in the header and on the welcome screen, plus `favicon.*`), then rebuild.

## Note on red-team "remote generation"

Some red-team strategies call Promptfoo's hosted API (`api.promptfoo.app`), even though the UI now says Xyberah. To keep all traffic inside your network, set `PROMPTFOO_DISABLE_REMOTE_GENERATION=true`.
