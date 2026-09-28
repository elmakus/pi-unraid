# M02-T01-R02 — independent repaired typed discovery/freeze review

Date: 2026-09-28  
Card: M02-T01  
Attempt: R02

## Exact subject

- Frozen result commit: 6f1fd3937abf78a8e44d491f50dfcad521495346
- Frozen result blob: 2ff7c71312857035816afed5c5331f1912e8eb1c
- Result path: implementation/workstreams/feature-paseo-update-distribution/results/M02-T01.md
- Implementation subject: cc16aa558e1366289868ec2eee266fd03ca615ca
- Acceptance Card: implementation/workstreams/feature-paseo-update-distribution/cards/M02-T01.md

## Independence

This review context did not materially produce or repair the exact M02-T01 implementation, repair, evidence or frozen result subject. It independently inspected the stable Card, binding requirements/ADR/plan authority, R01 findings, the exact repair diff and the exact implementation subject.

## Review result

No blocking finding remains.

- The R01 provenance defect is repaired at the typed freeze boundary: validate_component_provenance() is shared by typed normalization/freeze and final candidate validation, so repository, source-tag, npm-package and immutable artifact substitution fails closed before a frozen component record is emitted.
- The R01 acquisition-scope defect is repaired: current live managed components are routed through registry-derived typed npm, github_release, github_tag, oci and derived discovery dispatch before normalized freeze.
- GitHub release assets and Docker CLI tag/commit remain bounded GitHub-family variants; no apt/pip/cargo adapter was introduced.
- The repair changes only scripts/resolve-paseo-candidate.py and tests/test_paseo_candidate_resolver.py; no M02-T02/M02-T03 compatibility, fallback, lag-selection or infrastructure-blocking policy was introduced.

## Independent verification on exact implementation subject

Detached exact commit: cc16aa558e1366289868ec2eee266fd03ca615ca.

- python3 -m unittest tests.test_paseo_candidate_resolver -q -> 33/33 GREEN.
- python3 -m unittest tests.test_environment_capability_inventory_contract tests.test_managed_component_lifecycle -q -> 24/24 GREEN.
- python3 -m unittest discover -s tests -p "test_*.py" -q -> 407/407 GREEN.
- Reproduced pre-card baseline comparison against 1baadd009cacb66906abb144ca644c573c91416b: fixture candidate output is byte-identical.
- Candidate identity is unchanged at sha256:f6520024c285915eab782a99f28cf451ae37c092b05eff2e1cc5957838cda085.

## Verdict

GREEN.

The repaired exact subject satisfies the stable M02-T01 Card acceptance surface and is eligible for deterministic post-review finalization.
