# M03-T04 production authorization

- Date: 2026-09-23
- Card: `M03-T04 — Authorized production bootstrap and live functional acceptance`
- Authority: explicit current user authorization
- Status: **AUTHORIZED**

## Authorized scope

The user explicitly authorized execution of M03-T04 on Tower, including the Card-owned production effects:
- clean fast-forward of the production `pi-unraid` checkout to the exact approved workstream source;
- creation/reconciliation of the canonical Pi directories with the accepted target ownership;
- placement/reference of the existing dedicated Pi Codex-LB client credential through the accepted non-Git secret path;
- production build/start/restart/recreate of the `pi-unraid` service;
- persistent Pi home/session/provider configuration writes required by M03-T04;
- bounded explicitly named external Git/GitHub acceptance writes with readback.

The authorization does **not** extend M03-T04 beyond its existing Card contract. In particular it does not authorize Codex-LB product/source redesign or disruptive Docker-wide/host restart work owned by M03-T05.

## First real model interaction

For the first real M03-T04 model interaction, the user selected: `gpt6 sol low`.

This is an execution-time selection for M03-T04. Do not reinterpret it as authority to change the repository's permanent default model unless the existing accepted Card/authority independently requires such a change. Resolve the exact provider-visible model identifier from the live accepted Codex-LB/Pi interface without exposing secrets.
