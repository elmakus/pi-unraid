# M07-T07 ev5 interval-tolerance feasibility (worker, appends 21da0d9, no DONE)

READ-ONLY diagnostic (shipped source reads only). No implementation,
no proposal to implement, no tests/effects/source/state changes. No
blanket masking, snapshot-as-proof, PID trust, or final-bytes proof is
used or proposed. Main classifies the owning route; ev4 routing is not
authority. Refs: `config/pi-agent/bin/m07-t05-applied.py` (interval),
`scripts/paseo_candidate_muse_adapter.py:960-1060` (stage/start/check),
validator checks at :1353/:1480/:1509/:1558/:1590/:1655, R2 §1, Card.

## Current trip surface (exact)
- Watch set: recursive watches under staged root + direct watches on
  manifest + daemon config + parent-dir watches for the three
  (`serve`, ~:95-105). Mask `0x2|0x4|0x8|0x40|0x80|0x100|0x200|0x400|
  0x800|0x2000` (:93): MODIFY, ATTRIB, CLOSE_WRITE, MOVED_FROM/TO,
  CREATE, DELETE, DELETE_SELF, MOVE_SELF, UNMOUNT.
- Trip rule (`check`, ~:123-144): drain fd; any event on a non-parent wd
  trips; on parent wds only matching-name or critical
  (0x4000 Q_OVERFLOW | 0x8000 IGNORED | 0x400 DELETE_SELF | 0x800
  MOVE_SELF) trips; then `snapshot(root,rows) != baseline` or
  `inputs() != input_baseline` trips; any OSError/ValueError/KeyError
  trips. `ever_changed` is irreversible.
- ctime is baked in TWICE: per-row `snapshot` identities
  `[dev,ino,mode,ctime_ns,mtime_ns,size]` (:68) and `inputs()` identity
  `(dev,ino,mode,uid,ctime_ns,mtime_ns,size)` (:~117). A same-mode chmod
  trips via IN_ATTRIB event AND via both identity comparisons.
- Content anti-ABA already exists: snapshot re-hashes bytes/modes and
  aborts on read-race (`before/after fstat`, ~:47-58); event
  irreversibility preserves transient content-mutation evidence.

## Exact kernel observability limits (inotify ABI)
- `struct inotify_event = {wd, mask, cookie, len, name}`: NO pid, NO uid,
  NO before-image, NO operation detail beyond the event bit. `cookie`
  is nonzero ONLY for related MOVED_FROM/MOVED_TO pairs — ATTRIB,
  MODIFY, CREATE, DELETE carry cookie 0 and cannot be paired.
- An IN_ATTRIB from `chmod 0600` (same mode), `chown same-owner`,
  `utimens same-stamps`, `setxattr same-value`, or `chmod 0600→644`
  (real change) is BIT-IDENTICAL on the wire. Distinguishing needs a
  follow-up stat — i.e., a TOCTOU window between syscall and re-stat.
- Queue overflow (`IN_Q_OVERFLOW`, queue 16384 default) silently drops
  events; any counting scheme is void after overflow (code correctly
  keeps overflow terminal). Merging/coalescing is not guaranteed
  1:1 under load. Non-recursive watches (rglob at serve time only);
  snapshot covers the recursive gap.
- Actor attribution is IMPOSSIBLE in this API. fanotify (PID reporting),
  audit, eBPF are different privileged APIs = new capability; and PID
  still ≠ trust (recycling) per tasking.

## Distinguishability matrix (same-mode chmod vs each must-trip class)
- vs real mode change: same single IN_ATTRIB; stat mode differs →
  separable ONLY by racy re-stat (away+back inside the window is
  invisible). Forensic, not proof.
- vs same-owner chown / same-stamp touch / same-value xattr: SAME event
  AND SAME final full-stat (minus ctime) → INDISTINGUISHABLE even
  forensically. "ONLY chmod" cannot be isolated; the tolerable class is
  at best "metadata event with zero observable state delta".
- vs metadata ABA (chmod/chown away+back): final stat identical;
  only signal is event COUNT (2+ ATTRIBs vs 1) → void under
  overflow/merge; cannot be proven absent. Tasking's preserved
  transient-ABA detection therefore conflicts with tolerating
  single-ATTRIB on proof grounds.
- vs content mutate-restore: MODIFY/CLOSE_WRITE events + (restored)
  snapshot bytes → event pattern PROVES transience; preserved as long
  as content-event handling is untouched (it is, in any ATTRIB-scoped
  change).
- vs replacements/deletions/manifest/config-content: MOVE_SELF/
  DELETE_SELF/IGNORED + snapshot set/bytes + inputs bytes/lstat →
  independent paths, preserved untouched.

## Narrow-correction shape (described, NOT proposed for implementation)
A correction holding every preserved property except the single blind
spot would need, coordinately: (a) on IN_ATTRIB, synchronously re-stat
+ re-hash and trip on ANY delta in mode/uid/gid/size/mtime/content,
  any second event class, ATTRIB-count ≠ 1, or overflow/ignored/
  delete-self/move-self anywhere; (b) drop `st_ctime_ns` from BOTH
  snapshot identities (:68) AND inputs identity (:~117) (else the
  comparison still trips). Check call sites (6×) unchanged; content,
  owner-real-change, replace/delete, manifest/config, overflow paths
  byte-identical.
- Residual blind spot, exactly: single metadata event with fully
  identical final stat (same-mode chmod OR same-owner chown OR
  same-stamp touch OR same-value xattr OR perfectly restored
  metadata-ABA). Under a non-adversarial model (legitimate daemon
  normalization, no timing games) this reads as the daemon's chmod
  with practical certainty; under adversarial proof requirements it is
  unprovable within the supported set {inotify, stat, snapshot, event
  accounting} — and the tasking's constraints (no snapshot-as-proof,
  no PID trust, no final-bytes proof) close the remaining doors.
- Safety-equivalence verdict: the R2-explicit file/mode/content
  identity is untouched by such a change (same-mode chmod alters none
  of the three); what changes is implementation conservatism around
  ctime. Whether that delta equals safety equivalence is Main/Board's
  acceptance call, not this analysis. Any implementation remains a
  source change → validation-sources binding change → freeze/reconcile/
  authorized rebuild; NOT done here.
