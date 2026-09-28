import json, tempfile, unittest
from pathlib import Path
from scripts.paseo_known_good import load, rotate, guard_input

A="sha256:"+"a"*64; B="sha256:"+"b"*64; C="sha256:"+"c"*64; D="sha256:"+"d"*64

class KnownGoodTests(unittest.TestCase):
    def test_exact_schema_and_rotation(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"ledger.json"; p.write_text(json.dumps({"current":A,"previous_1":B,"previous_2":C}))
            ledger=load(p)
            self.assertEqual(rotate(ledger,D),{"current":D,"previous_1":A,"previous_2":B})
            self.assertEqual(rotate(ledger,A),ledger)
            with self.assertRaises(ValueError): rotate(ledger,B)
            with self.assertRaises(ValueError): rotate(ledger,C)

    def test_rejects_malformed_stale_or_duplicate_identity(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"ledger.json"
            for bad in [
                {"current":"accepted","previous_1":B,"previous_2":C},
                {"current":A,"previous_1":A,"previous_2":C},
                {"current":A,"previous_1":B,"previous_2":C,"previous_3":D},
            ]:
                p.write_text(json.dumps(bad))
                with self.assertRaises(ValueError): load(p)

    def test_guard_input_is_exact_and_unarmed(self):
        with tempfile.TemporaryDirectory() as d:
            anchor=Path(d)/"rollback.tar"; anchor.write_bytes(b"anchor")
            ledger={"current":A,"previous_1":B,"previous_2":C}
            out=guard_input(D,ledger,"sha256:"+"e"*64,anchor)
            self.assertEqual(out["state"],"unarmed")
            self.assertEqual(out["candidate_digest"],D)
            self.assertEqual(out["predecessor_digest"],A)
            self.assertEqual(out["rollback_anchor"],str(anchor.resolve()))
            with self.assertRaises(ValueError): guard_input(A,ledger,"sha256:"+"e"*64,anchor)
            anchor.unlink()
            with self.assertRaises(ValueError): guard_input(D,ledger,"sha256:"+"e"*64,anchor)
if __name__=="__main__": unittest.main()
