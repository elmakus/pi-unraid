import json, tempfile, unittest
from pathlib import Path
from scripts.paseo_known_good import (
    load, rotate, guard_input, atomic_write, migrate_legacy_ledger,
    commit_on_terminal, migrate_with_predecessor, validate_entry)

A="sha256:"+"a"*64; B="sha256:"+"b"*64; C="sha256:"+"c"*64; D="sha256:"+"d"*64
REPO="ghcr.io/elmakus/pi-unraid"

def oci(v, repo=REPO): return {"kind":"oci","digest":v,"repository":repo}
def local(v): return {"kind":"local","image_id":v}
def legacy(v): return {"kind":"legacy","image_id":v,"archive_sha256":B,
                       "config_digest":C,"state_identity":"legacy-state-1"}

class KnownGoodTests(unittest.TestCase):
    def test_exact_typed_schema_and_rotation(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"ledger.json"
            p.write_text(json.dumps({"current":oci(A),"previous_1":oci(B),"previous_2":oci(C)}))
            ledger=load(p)
            self.assertEqual(rotate(ledger,oci(D)),
                             {"current":oci(D),"previous_1":oci(A),"previous_2":oci(B)})
            self.assertEqual(rotate(ledger,oci(A)),ledger)
            with self.assertRaises(ValueError): rotate(ledger,oci(B))
            with self.assertRaises(ValueError): rotate(ledger,oci(C))

            rotated=rotate(ledger,oci(D))
            atomic_write(p,rotated)
            self.assertEqual(load(p),{"current":oci(D),"previous_1":oci(A),"previous_2":oci(B)})

            before=p.read_text()
            persisted=load(p)
            with self.assertRaises(ValueError): rotate(persisted,oci(A))
            self.assertEqual(p.read_text(),before)

    def test_rejects_untyped_ambiguous_or_duplicate_identity(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"ledger.json"
            for bad in [
                {"current":A,"previous_1":oci(B),"previous_2":oci(C)},
                {"current":{"kind":"weird","digest":A},"previous_1":oci(B),"previous_2":oci(C)},
                {"current":oci(A),"previous_1":oci(A),"previous_2":oci(C)},
                {"current":oci(A),"previous_1":oci(B),"previous_2":oci(C),"previous_3":oci(D)},
                {"current":{"kind":"oci","digest":A,"image_id":B},"previous_1":oci(B),"previous_2":oci(C)},
            ]:
                p.write_text(json.dumps(bad))
                with self.assertRaises(ValueError): load(p)

    def test_legacy_string_ledgers_migrate_coherently(self):
        old={"current":A,"previous_1":B,"previous_2":C}
        self.assertEqual(migrate_legacy_ledger(old),
                         {"current":{"kind":"oci","digest":A},
                          "previous_1":{"kind":"oci","digest":B},
                          "previous_2":{"kind":"oci","digest":C}})
        with self.assertRaises(ValueError):
            migrate_legacy_ledger({"current":A,"previous_1":B})
        with self.assertRaises(ValueError):
            migrate_legacy_ledger({"current":"accepted","previous_1":B,"previous_2":C})

    def test_commit_only_on_terminal_green(self):
        ledger={"current":oci(A),"previous_1":oci(B),"previous_2":oci(C)}
        self.assertEqual(commit_on_terminal(ledger,oci(D),transaction_status="GREEN")["current"],oci(D))
        self.assertEqual(commit_on_terminal(ledger,oci(D),transaction_status="committed")["current"],oci(D))
        for status in ("RED","RECOVERED","UNKNOWN","BLOCKED","FAIL"):
            with self.assertRaisesRegex(ValueError,"never rotates"):
                commit_on_terminal(ledger,oci(D),transaction_status=status)

    def test_typed_migration_binds_current(self):
        ledger={"current":oci(A),"previous_1":oci(B),"previous_2":oci(C)}
        out=migrate_with_predecessor(ledger,oci(D),
                                     predecessor_mapping={"kind":"oci","digest":A,"repository":REPO},
                                     transaction_status="GREEN")
        self.assertEqual(out["current"],oci(D))
        with self.assertRaises(ValueError):
            migrate_with_predecessor(ledger,oci(D),
                                     predecessor_mapping={"kind":"oci","digest":B,"repository":REPO},
                                     transaction_status="GREEN")
        with self.assertRaises(ValueError):
            migrate_with_predecessor(ledger,oci(D),
                                     predecessor_mapping={"kind":"local","image_id":A},
                                     transaction_status="GREEN")
        with self.assertRaises(ValueError):
            migrate_with_predecessor(ledger,oci(D),
                                     predecessor_mapping={"kind":"oci","digest":A,"repository":REPO},
                                     transaction_status="RED")

    def test_legacy_entries_carry_anchor(self):
        ledger={"current":legacy(A),"previous_1":oci(B),"previous_2":oci(C)}
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"ledger.json"; atomic_write(p,ledger); self.assertEqual(load(p),ledger)
        out=migrate_with_predecessor(ledger,oci(D),
                                     predecessor_mapping={"kind":"legacy","image_id":A,
                                                          "archive_sha256":B,"config_digest":C,
                                                          "state_identity":"legacy-state-1"},
                                     transaction_status="GREEN")
        self.assertEqual(out["previous_1"],legacy(A))
        bad=dict(out["previous_1"]); bad["archive_sha256"]=D
        with self.assertRaises(ValueError):
            migrate_with_predecessor({"current":legacy(A),"previous_1":oci(B),"previous_2":oci(C)},
                                     oci(D),
                                     predecessor_mapping={"kind":"legacy","image_id":A,
                                                          "archive_sha256":D,"config_digest":C,
                                                          "state_identity":"legacy-state-1"},
                                     transaction_status="GREEN")
        self.assertEqual(validate_entry(local(D)),local(D))

    def test_guard_input_is_exact_and_unarmed(self):
        with tempfile.TemporaryDirectory() as d:
            anchor=Path(d)/"rollback.tar"; anchor.write_bytes(b"anchor")
            ledger={"current":oci(A),"previous_1":oci(B),"previous_2":oci(C)}
            out=guard_input(D,ledger,"sha256:"+"e"*64,anchor)
            self.assertEqual(out["state"],"unarmed")
            self.assertEqual(out["candidate_digest"],D)
            self.assertEqual(out["predecessor_digest"],A)
            self.assertEqual(out["rollback_anchor"],str(anchor.resolve()))
            with self.assertRaises(ValueError): guard_input(A,ledger,"sha256:"+"e"*64,anchor)
            anchor.unlink()
            with self.assertRaises(ValueError): guard_input(D,ledger,"sha256:"+"e"*64,anchor)
if __name__=="__main__": unittest.main()
