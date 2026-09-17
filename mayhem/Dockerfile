# syntax=docker/dockerfile:1.7
#
# Commit-image Dockerfile (SMALL form) — builds ON TOP of the org base image
# (ghcr.io/savantenvs/base). The base provides debian + clang/llvm + libFuzzer + Python 3 + the
# identities + the build-contract ENV. pronto is a Python ontology library whose parser core is the
# native `fastobo` wheel plus its own pure-Python parsers/serializers; from Mayhem's point of view
# it is a Python target, so this image installs the Atheris harness engine (atheris) plus pronto and
# its test extra (coverage) into the base's system Python as root, then (as the non-root `mayhem`
# user) compiles the ELF launcher shims and runs the real unittest suite via build.sh / test.sh.
#
# Build (from the repo root):
#   DOCKER_BUILDKIT=1 docker build -f mayhem/Dockerfile \
#       --build-arg COMMIT=$(git rev-parse HEAD) \
#       [--build-arg SOURCE_DATE_EPOCH=$(date +%s)] \
#       -t pronto-commit:test .

FROM ghcr.io/savantenvs/base:20260621

ARG COMMIT
ARG REPO_URL
# SOURCE_DATE_EPOCH stays an ARG (available to build.sh); never bake it as ENV — an empty value
# breaks clang. build.sh unsets it when empty.
ARG SOURCE_DATE_EPOCH
# Declared for parity with the build contract; pronto has no first-party native code to sanitize.
ARG SANITIZER_FLAGS

# Atheris (the libFuzzer harness engine — builds a native module against the base's clang/libFuzzer)
# goes into the base's SYSTEM Python. PEP 668 marks that interpreter externally-managed, so
# --break-system-packages. This is the (networked) install step; build.sh deliberately does NOT
# pip-install, so its offline PATCH-tier re-run stays air-gapped. Atheris is pinned (3.1.0) for a
# reproducible engine.
USER root
RUN pip install --no-cache-dir --break-system-packages atheris==3.1.0

# Source enters from the build CONTEXT (the CI checkout): the FULL repo (incl. .git history)
# is copied to /mayhem as `mayhem`; build.sh builds in place.
WORKDIR /mayhem
COPY --chown=2000:2000 . /mayhem

# Install pronto itself + its runtime deps (chardet, fastobo, networkx, python-dateutil) and the
# test extra (coverage) so the harness can `import pronto` and the oracle can run the suite.
RUN pip install --no-cache-dir --break-system-packages . 'coverage[toml]'

# That install runs as root and leaves root-owned build artefacts in the tree (build/,
# pronto.egg-info/). The PATCH-tier clean-tree check re-runs `git clean -ffdX` as the non-root
# `mayhem` user, which then cannot remove them and fails the gate. Hand the tree back before
# dropping privileges.
RUN chown -R 2000:2000 /mayhem

USER mayhem

# Compile the ELF launcher shims (Mayhem needs an ELF target, not a .py).
RUN bash mayhem/build.sh

# Run pronto's real unittest suite at build time; a failing suite fails the build.
RUN if [ -f mayhem/test.sh ]; then bash mayhem/test.sh; else echo "no mayhem/test.sh"; fi

LABEL org.opencontainers.image.source="${REPO_URL}" \
      org.opencontainers.image.revision="${COMMIT}" \
      rlenv.tier="commit" \
      rlenv.source_date_epoch="${SOURCE_DATE_EPOCH}" \
      rlenv.user="mayhem"

USER mayhem
WORKDIR /mayhem
