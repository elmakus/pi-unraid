from __future__ import annotations
import importlib.util, tempfile, unittest
from pathlib import Path
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location("promotion",ROOT/"scripts"/"paseo_accepted_promotion.py")
P=importlib.util.module_from_spec(spec); assert spec.loader; spec.loader.exec_module(P)
A="sha256:"+"a"*64; B="sha256:"+"b"*64; C="sha256:"+"c"*64; D="sha256:"+"d"*64

class PromotionTests(unittest.TestCase):
    def run_promotion(self, reads, **kwargs):
        with tempfile.TemporaryDirectory() as td:
            with mock.patch.object(P,"inspect_digest",side_effect=reads) as inspect, mock.patch.object(P,"run_checked") as run:
                result=P.promote(repository="ghcr.io/elmakus/pi-unraid",alias="m05-fixture",
                    candidate_digest=B,expected_current_digest=A,output_path=Path(td)/"out.json",**kwargs)
                return result, inspect.call_count, run.call_args_list

    def test_nonproduction_promotion_and_readback(self):
        result,count,calls=self.run_promotion([A,A,B])
        self.assertEqual(result["readback_digest"],B); self.assertEqual(count,3)
        self.assertEqual(calls[0].args[0],["docker","buildx","imagetools","create","-t","ghcr.io/elmakus/pi-unraid:m05-fixture",f"ghcr.io/elmakus/pi-unraid@{B}"])

    def test_stale_candidate_fails_closed(self):
        with tempfile.TemporaryDirectory() as td, mock.patch.object(P,"inspect_digest",return_value=C), mock.patch.object(P,"run_checked") as run:
            with self.assertRaises(P.PromotionError):
                P.promote(repository="ghcr.io/elmakus/pi-unraid",alias="m05-fixture",candidate_digest=B,expected_current_digest=A,output_path=Path(td)/"o")
            run.assert_not_called()

    def test_newer_candidate_race_fails_closed(self):
        with tempfile.TemporaryDirectory() as td, mock.patch.object(P,"inspect_digest",side_effect=[A,C]), mock.patch.object(P,"run_checked") as run:
            with self.assertRaises(P.PromotionError):
                P.promote(repository="ghcr.io/elmakus/pi-unraid",alias="m05-fixture",candidate_digest=B,expected_current_digest=A,output_path=Path(td)/"o")
            run.assert_not_called()

    def test_production_rejects_without_green_final_gate(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(P.PromotionError):
                P.promote(repository="ghcr.io/elmakus/pi-unraid",alias="accepted",candidate_digest=B,expected_current_digest=A,output_path=Path(td)/"o")

    def test_production_rejects_without_matching_armed_guard(self):
        gate={"status":"GREEN","candidate_digest":B,"guard_binding_digest":D}
        guard={"state":"armed","candidate_digest":C,"previous_digest":A,"rollback_digest":A,"config_digest":D,"binding_digest":D}
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(P.PromotionError):
                P.promote(repository="ghcr.io/elmakus/pi-unraid",alias="accepted",candidate_digest=B,expected_current_digest=A,output_path=Path(td)/"o",final_gate=gate,guard=guard)

    def test_digest_mismatch_after_promotion_fails(self):
        with tempfile.TemporaryDirectory() as td, mock.patch.object(P,"inspect_digest",side_effect=[A,A,C]), mock.patch.object(P,"run_checked"):
            with self.assertRaises(P.PromotionError):
                P.promote(repository="ghcr.io/elmakus/pi-unraid",alias="m05-fixture",candidate_digest=B,expected_current_digest=A,output_path=Path(td)/"o")

    def test_mutable_rollback_tag_rejected(self):
        with self.assertRaises(P.PromotionError): P.validate_rollback_identity("ghcr.io/elmakus/pi-unraid:accepted")

if __name__=="__main__": unittest.main()
