# Setting up Xyberah

This guide takes you from a fresh machine to Xyberah running at http://localhost:3000, then through your first eval and red-team run. Part 1 is for Windows, part 2 is for a Linux server; after that the steps are the same for both.

You build the image yourself from this repository. The first build takes 20–40 minutes and needs internet access to Docker Hub, GitHub, npm, PyPI and download.pytorch.org.

## What you need

| | Minimum |
|---|---|
| CPU | 64-bit x86 (amd64), 4 cores |
| Memory | 16 GB RAM in the machine, at least 8 GB of it for Docker (12 GB recommended) |
| Disk | 30 GB free (the image is about 5 GB; build caches take the rest) |
| Model access | An API key for at least one model provider (OpenAI, Anthropic, Azure OpenAI, etc.), or a local model server such as Ollama |

---

## Part 1 — Windows 10/11 with Docker Desktop

### 1. Install the tools

1. Install **Docker Desktop**: https://www.docker.com/products/docker-desktop/ — keep the default "Use WSL 2" option. Restart Windows if asked.
2. Install **Git** (to download this repository). In PowerShell:

```bash
winget install --id Git.Git -e
```

### 2. Give Docker enough memory

Docker on Windows runs inside WSL 2, which by default may not get enough memory to build the image.

1. Open the WSL settings file in Notepad:

```bash
notepad "$env:USERPROFILE\.wslconfig"
```

2. Put this in it and save (use about 75% of your RAM for `memory`):

```ini
[wsl2]
memory=12GB
swap=8GB
```

3. Apply it in this order — **quit Docker Desktop first** (tray icon → Quit Docker Desktop), then:

```bash
wsl --shutdown
```

4. Start Docker Desktop again and wait until it shows **Engine running**.

> If you run `wsl --shutdown` while Docker Desktop is open, every `docker` command fails with `request returned 500 Internal Server Error ... dockerDesktopLinuxEngine`. Quit and reopen Docker Desktop to fix it.

### 3. Check Docker works

```bash
docker version
```

You should see both a `Client:` and a `Server:` section. Then continue with **Part 3**.

---

## Part 2 — Linux server (Ubuntu/Debian/RHEL)

1. Install Docker Engine and the Compose plugin by following https://docs.docker.com/engine/install/ for your distribution.
2. Let your user run Docker without sudo (log out and in afterwards):

```bash
sudo usermod -aG docker $USER
```

3. Install Git with your package manager (`sudo apt install git` or `sudo dnf install git`).
4. Check Docker works:

```bash
docker version
```

If the server only allows outbound traffic through a TLS-inspecting proxy, see "Corporate proxy" under Troubleshooting before building.

---

## Part 3 — Build and start Xyberah

### 1. Download the code

```bash
git clone https://github.com/abdulmyid/Xyberah-AI-Redteaming-VA.git
```

```bash
cd Xyberah-AI-Redteaming-VA
```

### 2. Build the image

```bash
docker build --platform linux/amd64 -t xyberah:0.124.1 -t xyberah:latest .
```

The build fetches Promptfoo, applies the Xyberah branding, extracts the garak probe prompts and compiles the ModelAudit scanner. It ends with `naming to docker.io/library/xyberah:latest`.

### 3. Add your model API keys

Open `docker-compose.yml` and add the keys your tests need under `environment:`, for example:

```yaml
    environment:
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      PROMPTFOO_DISABLE_TELEMETRY: "1"
```

Then create a file named `.env` next to `docker-compose.yml` holding the actual values (it is git-ignored, so the keys never get committed):

```ini
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

Red-team grading uses an LLM too. Without an `OPENAI_API_KEY` (or a grading provider set in your config), graded tests fail with "API key is not set".

To keep all red-team traffic inside your network (Xyberah otherwise uses Promptfoo's hosted service for some attack generation), also add:

```yaml
      PROMPTFOO_DISABLE_REMOTE_GENERATION: "true"
```

### 4. Start it

```bash
docker compose up -d
```

Open http://localhost:3000. You should see "Welcome to Xyberah". The container restarts automatically with Docker unless you stop it with `docker compose down`.

Eval history is kept in the Docker volume `xyberah-data`, so it survives restarts and image upgrades.

---

## Part 4 — First runs

### A red-team scan from the web UI

1. Click **Create Red Team**.
2. **Target**: choose your model provider or HTTP endpoint and fill in its details.
3. **Application details**: describe what your app does. This steers the attacks.
4. **Plugins**: pick the risks to test. The four **Garak** groups contain NVIDIA garak's probe library.
5. **Strategies**: leave the defaults to start.
6. **Review** → **Run**. When it finishes, open the report to see failures by category and severity.

### The same from the command line

Save this as `redteam.yaml` in a folder (replace the target with yours):

```yaml
description: First red-team scan
targets:
  - id: openai:gpt-4.1-mini
redteam:
  purpose: Customer support assistant for an online shop
  numTests: 5
  plugins:
    - garak:all
    - harmful
  strategies:
    - jailbreak
```

From that folder:

```bash
docker run --rm -v "${PWD}:/work" -w /work --env-file /path/to/Xyberah-AI-Redteaming-VA/.env xyberah:latest xyberah redteam run -c redteam.yaml
```

On Linux the container user may not be allowed to write to your folder; if you see `EACCES`, run `chmod o+w .` in that folder first (or add `-u root` to the command).

### Scan a model file

In the UI open **Model Audit**, add the path of a model file inside the container (mount a folder into the container first), and click **Start Security Scan**. Or from the command line:

```bash
docker run --rm -v "${PWD}:/models" xyberah:latest modelaudit scan /models/model.pkl
```

---

## Updating

```bash
git pull
```

```bash
docker build --platform linux/amd64 -t xyberah:0.124.1 -t xyberah:latest .
```

```bash
docker compose up -d --force-recreate
```

Your eval history is kept. To move to a newer Promptfoo or garak release, see "Upgrading" in the [README](README.md).

## Troubleshooting

| Symptom | Fix |
|---|---|
| `500 Internal Server Error ... dockerDesktopLinuxEngine` | Docker Desktop lost its WSL VM (usually after `wsl --shutdown`). Quit and reopen Docker Desktop. |
| Build stops with `JavaScript heap out of memory` or gets killed | Docker has too little memory. Raise `memory` in `.wslconfig` (Windows) or add RAM/swap (Linux). |
| `[upsell] ... anchor matched 0 times` or `[garak] ... expected 1 match` | The upstream Promptfoo code changed (only after changing `PROMPTFOO_VERSION`). Update the anchor text in the named script. |
| Red-team results all fail with "API key is not set" | Add `OPENAI_API_KEY` (used for grading) or configure a grading provider. |
| Port 3000 already in use | Change `"3000:3000"` in `docker-compose.yml` to e.g. `"8080:3000"` and use http://localhost:8080. |
| Corporate proxy / TLS inspection breaks the build | Add `--secret id=ca,src=/path/to/ca-bundle.crt` to `docker build`. The certificate is used only during the build. |
