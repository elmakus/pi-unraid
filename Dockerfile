# syntax=docker/dockerfile:1

ARG NODE_IMAGE="node:24-bookworm-slim@sha256:0e0ff40c39bc087845bfb27465a0df4ea419520094bc35842ff83dd8cbe6f9b6"
FROM ${NODE_IMAGE}

ARG PI_SEED_VERSION="0.87.1"

LABEL org.opencontainers.image.title="pi-unraid" \
      org.opencontainers.image.description="Phase 1 Pi Coding Agent base for Unraid" \
      io.pi-unraid.pi-seed-version="${PI_SEED_VERSION}"

ENV DEBIAN_FRONTEND=noninteractive \
    PI_UNRAID_SEED_VERSION="${PI_SEED_VERSION}"

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        build-essential \
        ca-certificates \
        curl \
        fd-find \
        git \
        git-lfs \
        gh \
        gosu \
        gzip \
        jq \
        less \
        openssh-client \
        procps \
        python3 \
        python3-pip \
        ripgrep \
        sudo \
        tar \
        unzip \
        xz-utils \
        zip \
    && rm -rf /var/lib/apt/lists/* \
    && ln -s /usr/bin/fdfind /usr/local/bin/fd \
    && git lfs install --system

RUN npm install -g --ignore-scripts "@earendil-works/pi-coding-agent@${PI_SEED_VERSION}" \
    && pi --version | grep -F "${PI_SEED_VERSION}"

RUN groupmod --new-name pi node \
    && usermod --login pi --home /home/pi --shell /bin/bash node \
    && install -d -o pi -g pi -m 0755 /home/pi /projects /worktrees \
    && printf 'pi ALL=(ALL) NOPASSWD:ALL\n' > /etc/sudoers.d/pi \
    && chmod 0440 /etc/sudoers.d/pi

ENV HOME=/home/pi \
    USER=pi \
    LOGNAME=pi

COPY --chmod=0755 scripts/container-entrypoint.sh /usr/local/bin/pi-unraid-entrypoint

WORKDIR /home/pi

ENTRYPOINT ["/usr/local/bin/pi-unraid-entrypoint"]
CMD ["sleep", "infinity"]
