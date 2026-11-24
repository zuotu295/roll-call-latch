# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

import json
import re
from xml.etree import ElementTree
from genlayer import Address, TreeMap, gl, u256


def vote_snapshot(xml: bytes, roll: int, year: int) -> str:
    if len(xml) > 300000 or b"<!DOCTYPE" in xml.upper() or b"<!ENTITY" in xml.upper():
        raise gl.vm.UserError("Unsupported vote document")
    root = ElementTree.fromstring(xml)
    meta = root.find("vote-metadata")
    if root.tag != "rollcall-vote" or meta is None:
        raise gl.vm.UserError("Official vote metadata unavailable")
    totals = meta.find("vote-totals/totals-by-vote")
    result = meta.findtext("vote-result", "").strip()
    if (meta.findtext("chamber") != "U.S. House of Representatives"
            or meta.findtext("rollcall-num") != str(roll)
            or not meta.findtext("action-date", "").endswith("-" + str(year))
            or meta.findtext("vote-type") != "YEA-AND-NAY" or totals is None
            or result not in ("Passed", "Failed")):
        raise gl.vm.UserError("Unsupported or mismatched roll call")
    yea, nay = [int(totals.findtext(key, "-1")) for key in ("yea-total", "nay-total")]
    if min(yea, nay) < 0 or not 1 <= yea + nay <= 450:
        raise gl.vm.UserError("Official vote totals unavailable")
    return json.dumps({"yea": yea, "nay": nay, "result": result}, separators=(",", ":"))


class RollCallLatch(gl.Contract):
    sponsor: Address
    cases: TreeMap[str, str]

    def __init__(self):
        self.sponsor = gl.message.sender_address

    @gl.public.write
    def bind(self, key: str, year: u256, roll: u256, min_yea: u256):
        if gl.message.sender_address != self.sponsor:
            raise gl.vm.UserError("Only the sponsor can bind a rule")
        if not re.fullmatch(r"[a-z0-9-]{3,40}", key) or not 1990 <= year <= 2100 or not 1 <= roll <= 9999 or not 1 <= min_yea <= 450:
            raise gl.vm.UserError("Invalid rule parameters")
        if key in self.cases:
            raise gl.vm.UserError("Rule is already bound")
        self.cases[key] = json.dumps({"year": int(year), "roll": int(roll), "min_yea": int(min_yea),
                                     "state": "PENDING"}, separators=(",", ":"))

    @gl.public.write
    def settle(self, key: str) -> str:
        rule = json.loads(self.cases.get(key, "{}"))
        if rule.get("state") != "PENDING":
            raise gl.vm.UserError("No pending rule")
        year, roll = rule["year"], rule["roll"]
        url = f"https://clerk.house.gov/evs/{year}/roll{roll:03d}.xml"

        def observe() -> str:
            response = gl.nondet.web.get(url)
            return vote_snapshot(response.body, roll, year)

        agreed = json.loads(gl.eq_principle.strict_eq(observe))
        rule["evidence"] = agreed
        rule["state"] = "ACTIVATED" if agreed["result"] == "Passed" and agreed["yea"] >= rule["min_yea"] else "CLOSED"
        self.cases[key] = json.dumps(rule, separators=(",", ":"))
        return self.cases[key]

    @gl.public.view
    def get_rule(self, key: str) -> str:
        return self.cases.get(key, "")
