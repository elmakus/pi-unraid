# M04-T03 — persistent-state round-trip evidence

Date: 2026-09-28

## Tower proof

The production Paseo HOME was used only as a read source to seed a disposable representative clone. The proof copied and hashed persistent identity/configuration surfaces without recording secret bytes: config.json, daemon-keypair.json, server-id, and available projects/workspaces registries.

Immutable local runtime identities verified by Docker image-ID readback:
- candidate: sha256:e3bf3c6259c2af6816579fc4cfec3c4bab417561200146620f2a1a92985b616a
- previous/rollback: sha256:4bf8bb0cc3c9bd9172f43bf56ea35c52ceb5d5fa3f0ec6ef5ed936e1ea213d30

The disposable clone was mounted only into isolated containers with network=none, read-only rootfs and tmpfs /tmp,/run. No Docker socket, host-control credential, Codex-LB credential or production HOME mount was exposed.

Observed direct path:
1. clone actual accepted baseline;
2. candidate opens the clone successfully;
3. representative candidate state marker is written;
4. previous runtime opens the same candidate-modified clone successfully;
5. candidate-state marker hash remains identical.

Result: PASS for baseline_clone_isolated, candidate_state_mutation, previous_runtime_reopen and direct_skip_path.

Negative ordinary-channel fixture with an intentionally incompatible persistent-state marker returned structured BLOCKED with exit code 3 before either runtime was launched.

## Verification

- focused tests: 4/4 GREEN
- py_compile: GREEN
- git diff --check: GREEN
- full repository unit suite: 461/461 GREEN from /root/pi-unraid-m04-r02, outside the system temporary directory
- production container and production persistent state were not mutated.

## R01 correction rerun

R01 found that the original representative marker was written by the validator host after the candidate stopped. The corrected proof writes the representative state artifact from inside the still-running exact candidate container, then stops that candidate and reopens the same cloned HOME with the previous runtime.

Tower rerun against the same actual accepted baseline and immutable identities:
- candidate: sha256:e3bf3c6259c2af6816579fc4cfec3c4bab417561200146620f2a1a92985b616a
- previous/rollback: sha256:4bf8bb0cc3c9bd9172f43bf56ea35c52ceb5d5fa3f0ec6ef5ed936e1ea213d30
- candidate-owned state marker SHA-256: af30cbf145e7c225d59633b2fb7bf0805cfaa85a1d1429b614d79b23b9a8fbdc
- corrected direct A -> C -> A proof: PASS
- incompatible-transition fixture: BLOCKED / rc=3 before runtime launch
- focused tests: 4/4 GREEN
- py_compile: GREEN
- git diff --check: GREEN
- full repository suite: 461/461 GREEN from /root/pi-unraid-m04-r02

The disposable clone remained separate from production state; production HOME was read only to seed the clone and no production container/tag/guard/credential was mutated or exposed.
