# syntax=docker/dockerfile:1

FROM ghcr.io/getpaseo/paseo@sha256:d413ff361bc4018d559da3d517a6d5a9eaca721fbb1b71ae8df3dcf7a965c136

LABEL org.opencontainers.image.title="pi-unraid Paseo child image" \
      org.opencontainers.image.description="Frozen Paseo/Pi child-image foundation for Unraid" \
      io.pi-unraid.candidate-id="sha256:b4e0c1e7c276371b84abd5c9aa7e325705b71349fe614b76855510dabf350b69" \
      io.pi-unraid.paseo-version="0.9.2" \
      io.pi-unraid.pi-version="0.87.1" \
      io.pi-unraid.playwright-version="1.63.0"

ENV DEBIAN_FRONTEND=noninteractive \
    PI_UNRAID_CANDIDATE_ID="sha256:b4e0c1e7c276371b84abd5c9aa7e325705b71349fe614b76855510dabf350b69" \
    PI_UNRAID_PI_VERSION="0.87.1" \
    PI_UNRAID_PLAYWRIGHT_VERSION="1.63.0" \
    PI_UNRAID_GH_VERSION="2.101.0" \
    PI_UNRAID_DOCKER_CLI_VERSION="29.8.1" \
    PI_UNRAID_DOCKER_COMPOSE_VERSION="5.5.1" \
    PLAYWRIGHT_BROWSERS_PATH="/opt/ms-playwright"

# General development/browser prerequisites belong to the exact child-image
# package graph. Independently versioned tools below are pinned to the frozen
# candidate and never re-resolve a "latest" channel during build.
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
      build-essential \
      dnsutils \
      fd-find \
      git-lfs \
      gzip \
      iproute2 \
      jq \
      less \
      netcat-openbsd \
      python3 \
      python3-pip \
      ripgrep \
      unzip \
      util-linux \
      xauth \
      xvfb \
      xz-utils \
      zip; \
    rm -rf /var/lib/apt/lists/*; \
    if [ ! -e /usr/local/bin/fd ]; then ln -s /usr/bin/fdfind /usr/local/bin/fd; fi; \
    git lfs install --system; \
    command -v Xvfb

RUN set -eux; \
    npm install -g --ignore-scripts \
      "@earendil-works/pi-coding-agent@${PI_UNRAID_PI_VERSION}" \
      "playwright@${PI_UNRAID_PLAYWRIGHT_VERSION}"; \
    test "$(pi --version)" = "${PI_UNRAID_PI_VERSION}"; \
    test "$(playwright --version)" = "Version ${PI_UNRAID_PLAYWRIGHT_VERSION}"; \
    install -d -m 0755 "${PLAYWRIGHT_BROWSERS_PATH}"; \
    playwright install --with-deps chromium; \
    chmod -R a+rX "${PLAYWRIGHT_BROWSERS_PATH}"; \
    npm cache clean --force

RUN set -eux; \
    curl -fsSL \
      "https://github.com/cli/cli/releases/download/v${PI_UNRAID_GH_VERSION}/gh_${PI_UNRAID_GH_VERSION}_linux_amd64.tar.gz" \
      -o /tmp/gh.tar.gz; \
    echo "9bca2d1c16825f109907a23307628a2f0698fbf99662b73a5cf0b020293072b8  /tmp/gh.tar.gz" | sha256sum -c -; \
    tar -xzf /tmp/gh.tar.gz -C /tmp; \
    install -m 0755 "/tmp/gh_${PI_UNRAID_GH_VERSION}_linux_amd64/bin/gh" /usr/local/bin/gh; \
    test "$(gh --version | head -n1 | awk '{print $3}')" = "${PI_UNRAID_GH_VERSION}"; \
    rm -rf /tmp/gh.tar.gz "/tmp/gh_${PI_UNRAID_GH_VERSION}_linux_amd64"

# docker/cli does not publish a GitHub release asset digest for this release.
# M01-T01 therefore froze the exact version + source commit identity; the build
# consumes that exact versioned stable archive and verifies the installed version.
RUN set -eux; \
    curl -fsSL \
      "https://download.docker.com/linux/static/stable/x86_64/docker-${PI_UNRAID_DOCKER_CLI_VERSION}.tgz" \
      -o /tmp/docker.tgz; \
    tar -xzf /tmp/docker.tgz -C /tmp; \
    install -m 0755 /tmp/docker/docker /usr/local/bin/docker; \
    docker --version | grep -F "Docker version ${PI_UNRAID_DOCKER_CLI_VERSION},"; \
    rm -rf /tmp/docker /tmp/docker.tgz

RUN set -eux; \
    install -d -m 0755 /usr/local/lib/docker/cli-plugins; \
    curl -fsSL \
      "https://github.com/docker/compose/releases/download/v${PI_UNRAID_DOCKER_COMPOSE_VERSION}/docker-compose-linux-x86_64" \
      -o /tmp/docker-compose; \
    echo "db1889184726840f75c4f9c001048430d4f25b3be3cb084d3ddd762bc0aed576  /tmp/docker-compose" | sha256sum -c -; \
    install -m 0755 /tmp/docker-compose /usr/local/lib/docker/cli-plugins/docker-compose; \
    ln -sf /usr/local/lib/docker/cli-plugins/docker-compose /usr/local/bin/docker-compose; \
    test "$(docker compose version --short)" = "${PI_UNRAID_DOCKER_COMPOSE_VERSION}"; \
    rm -f /tmp/docker-compose

# Intentionally inherit Paseo's HOME=/home/paseo, root-capable setup entrypoint,
# gosu drop to the non-root paseo user, server command, healthcheck and volume
# contract from the exact parent image. Do not add USER/ENTRYPOINT/CMD here.
WORKDIR /workspace
