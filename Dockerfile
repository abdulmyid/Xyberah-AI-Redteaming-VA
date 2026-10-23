# syntax=docker/dockerfile:1
# Xyberah - white-labelled build of Promptfoo (MIT, https://github.com/promptfoo/promptfoo)
ARG PROMPTFOO_VERSION=0.124.1
# Red-team prompts from NVIDIA garak (Apache-2.0, https://github.com/NVIDIA/garak)
ARG GARAK_VERSION=0.17.0
# Model scanner behind the "Model Audit" page (https://pypi.org/project/modelaudit/)
ARG MODELAUDIT_VERSION=0.2.52

# Optional: corporate proxy / custom CA for the build only (never baked into the image):
#   docker build --secret id=ca,src=/path/to/ca-bundle.crt ...

# ---- 1. fetch upstream source and apply branding --------------------------
FROM alpine:3.22 AS source
ARG PROMPTFOO_VERSION
RUN --mount=type=secret,id=ca,required=false if [ -f /run/secrets/ca ]; then export SSL_CERT_FILE=/run/secrets/ca NODE_EXTRA_CA_CERTS=/run/secrets/ca GIT_SSL_CAINFO=/run/secrets/ca; fi; apk add --no-cache git python3 && \
    git clone --depth 1 --branch ${PROMPTFOO_VERSION} https://github.com/promptfoo/promptfoo /src
COPY branding /branding
COPY garak /garak
RUN python3 /branding/apply-upsell.py /src && \
    python3 /garak/apply-garak.py /src /garak && \
    python3 /branding/apply-branding.py /src /branding/assets

# ---- 1b. extract garak probe prompts (garak itself is not shipped) ---------
FROM python:3.12-slim AS garak-data
ARG GARAK_VERSION
COPY garak/extract_garak.py /extract_garak.py
RUN --mount=type=cache,target=/root/.cache/pip --mount=type=secret,id=ca,required=false \
    if [ -f /run/secrets/ca ]; then export PIP_CERT=/run/secrets/ca REQUESTS_CA_BUNDLE=/run/secrets/ca SSL_CERT_FILE=/run/secrets/ca; fi; \
    pip install --root-user-action=ignore --extra-index-url https://download.pytorch.org/whl/cpu "garak==${GARAK_VERSION}" && \
    python /extract_garak.py /out

# ---- 2. upstream build, unchanged except for branding ---------------------
FROM node:24.21.0-alpine AS base
RUN --mount=type=secret,id=ca,required=false if [ -f /run/secrets/ca ]; then export SSL_CERT_FILE=/run/secrets/ca NODE_EXTRA_CA_CERTS=/run/secrets/ca GIT_SSL_CAINFO=/run/secrets/ca; fi; apk upgrade --no-cache
RUN addgroup -S xyberah && adduser -S xyberah -G xyberah
ARG PYTHON_VERSION=
RUN --mount=type=secret,id=ca,required=false if [ -f /run/secrets/ca ]; then export SSL_CERT_FILE=/run/secrets/ca NODE_EXTRA_CA_CERTS=/run/secrets/ca GIT_SSL_CAINFO=/run/secrets/ca; fi; apk add --no-cache "python3${PYTHON_VERSION:+~=${PYTHON_VERSION}}" py3-pip py3-setuptools curl && \
    ln -sf python3 /usr/bin/python

FROM base AS builder
RUN --mount=type=secret,id=ca,required=false if [ -f /run/secrets/ca ]; then export SSL_CERT_FILE=/run/secrets/ca NODE_EXTRA_CA_CERTS=/run/secrets/ca GIT_SSL_CAINFO=/run/secrets/ca; fi; apk add --no-cache libc6-compat
WORKDIR /app
ARG VITE_PUBLIC_BASENAME
ARG PROMPTFOO_REMOTE_API_BASE_URL
ENV VITE_IS_HOSTED=1 \
    VITE_TELEMETRY_DISABLED=1 \
    VITE_PUBLIC_BASENAME=${VITE_PUBLIC_BASENAME} \
    PROMPTFOO_REMOTE_API_BASE_URL=${PROMPTFOO_REMOTE_API_BASE_URL}
COPY --from=source /src/package.json /src/package-lock.json ./
COPY --from=source /src/src/app/package.json ./src/app/package.json
COPY --from=source /src/site/package.json ./site/package.json
RUN --mount=type=cache,target=/root/.npm --mount=type=secret,id=ca,required=false \
    if [ -f /run/secrets/ca ]; then export SSL_CERT_FILE=/run/secrets/ca NODE_EXTRA_CA_CERTS=/run/secrets/ca GIT_SSL_CAINFO=/run/secrets/ca; fi; npm ci --install-links --include=peer --ignore-scripts && \
    npm rebuild ./node_modules/esbuild
COPY --from=source /src/ .
# Build steps run one after another (upstream runs them in parallel, which needs ~12 GB RAM)
RUN export NODE_OPTIONS=--max-old-space-size=6144 && \
    npx tsdown && \
    npm run build:app && \
    npm run postbuild

# ---- 2b. ModelAudit CLI ----------------------------------------------------
# Alpine's python3 is too new for modelaudit (<3.14) and its picklescan
# dependency only ships as Rust source on musl, so build it in its own
# Python 3.12 venv here and copy the result into the runtime image.
FROM base AS modelaudit
ARG MODELAUDIT_VERSION
ENV UV_PYTHON_INSTALL_DIR=/opt/uv-python
RUN --mount=type=cache,target=/root/.cache/uv --mount=type=secret,id=ca,required=false \
    if [ -f /run/secrets/ca ]; then export SSL_CERT_FILE=/run/secrets/ca UV_NATIVE_TLS=1; fi; \
    apk add --no-cache uv build-base rust cargo && \
    uv venv --python 3.12 /opt/modelaudit && \
    VIRTUAL_ENV=/opt/modelaudit uv pip install "modelaudit==${MODELAUDIT_VERSION}" && \
    /opt/modelaudit/bin/modelaudit --version

# ---- 3. runtime ------------------------------------------------------------
FROM base AS server
ARG PROMPTFOO_VERSION
LABEL org.opencontainers.image.title="Xyberah" \
      org.opencontainers.image.vendor="Xyberah" \
      org.opencontainers.image.url="https://xyberah.com" \
      org.opencontainers.image.version="${PROMPTFOO_VERSION}" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.description="Xyberah LLM evaluation & red teaming (based on Promptfoo, MIT)"
WORKDIR /app
COPY --from=builder --chown=xyberah:xyberah /app/node_modules ./node_modules
COPY --from=builder --chown=xyberah:xyberah /app/package.json ./package.json
COPY --from=builder --chown=xyberah:xyberah /app/dist ./dist
# MIT licence notice must ship with the software
COPY --from=source /src/LICENSE /app/LICENSE
# garak prompt data + its Apache-2.0 licence (in /app/garak)
COPY --from=garak-data /out /app/garak
COPY --from=modelaudit /opt/uv-python /opt/uv-python
COPY --from=modelaudit /opt/modelaudit /opt/modelaudit

RUN ln -s /app /app/node_modules/promptfoo && \
    chown -h xyberah:xyberah /app/node_modules/promptfoo && \
    ln -s /app/dist/src/entrypoint.js /usr/local/bin/xyberah && \
    ln -s /opt/modelaudit/bin/modelaudit /usr/local/bin/modelaudit && \
    mkdir -p /home/xyberah/.promptfoo && chown xyberah:xyberah /home/xyberah/.promptfoo

ENV API_PORT=3000 \
    HOST=0.0.0.0 \
    PROMPTFOO_SELF_HOSTED=1 \
    PROMPTFOO_RUNNING_IN_DOCKER=1 \
    PROMPTFOO_OFFICIAL_DOCKER_IMAGE=0 \
    PROMPTFOO_DISABLE_TELEMETRY=1 \
    PROMPTFOO_DISABLE_UPDATE=1 \
    XYBERAH_GARAK_DATA_DIR=/app/garak

USER xyberah
EXPOSE 3000
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s CMD node -e "require('node:http').get('http://127.0.0.1:3000/health',r=>process.exit(r.statusCode<400?0:1)).on('error',()=>process.exit(1))"
CMD ["node", "dist/src/server/index.js"]
