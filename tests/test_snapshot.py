"""Unit tests for the source parser; signed-chain evidence is separate."""
import importlib.util
import json
from pathlib import Path
import sys
import types
import unittest

sdk = types.ModuleType("genlayer")
sdk.Address, sdk.TreeMap, sdk.u256 = str, dict, int
sdk.gl = types.SimpleNamespace(Contract=object, vm=types.SimpleNamespace(UserError=ValueError),
                               public=types.SimpleNamespace(write=lambda f: f, view=lambda f: f))
sys.modules["genlayer"] = sdk
spec = importlib.util.spec_from_file_location("roll_call_latch", Path(__file__).resolve().parents[1] / "contracts/roll_call_latch.py")
contract = importlib.util.module_from_spec(spec)
spec.loader.exec_module(contract)
VOTE = b"""<rollcall-vote><vote-metadata>
<chamber>U.S. House of Representatives</chamber><rollcall-num>2</rollcall-num>
<action-date>10-Jan-2024</action-date><vote-type>YEA-AND-NAY</vote-type><vote-result>Passed</vote-result>
<vote-totals><totals-by-vote><yea-total>213</yea-total><nay-total>200</nay-total></totals-by-vote></vote-totals>
</vote-metadata></rollcall-vote>"""


class VoteTests(unittest.TestCase):
    def test_canonical_tuple(self):
        self.assertEqual(json.loads(contract.vote_snapshot(VOTE, 2, 2024)), {"yea": 213, "nay": 200, "result": "Passed"})

    def test_mismatched_roll_and_year_fail(self):
        for roll, year in ((3, 2024), (2, 2023)):
            with self.assertRaisesRegex(ValueError, "mismatched"):
                contract.vote_snapshot(VOTE, roll, year)

    def test_unsupported_xml_and_totals_fail(self):
        with self.assertRaisesRegex(ValueError, "Unsupported vote document"):
            contract.vote_snapshot(b"<!DOCTYPE rollcall-vote>" + VOTE, 2, 2024)
        with self.assertRaisesRegex(ValueError, "totals unavailable"):
            contract.vote_snapshot(VOTE.replace(b"213", b"999"), 2, 2024)
