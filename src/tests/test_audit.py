"""
Tests for the deterministic argument auditor: graph checks, the
/api/argument/audit route, and the `dianoia audit` CLI command.
"""

import json

from fastapi.testclient import TestClient

from main import app
from schemas.step import Step
from services.audit import audit_argument

client = TestClient(app)


def step(symbol, proposition="A proposition.", justifiers=None):
    return Step(symbol=symbol, proposition=proposition,
                justifiers=justifiers or [], truth_score="")


class TestAuditArgument:
    """Deterministic graph checks"""

    def test_clean_argument_is_satisfied(self):
        steps = [step("1"), step("2"), step("3", justifiers=["1", "2"])]
        result = audit_argument(steps)
        assert result.satisfied is True
        assert result.findings == []

    def test_empty_argument_is_satisfied(self):
        result = audit_argument([])
        assert result.satisfied is True
        assert result.findings == []

    def test_orphan_step_flagged_as_connectivity(self):
        steps = [step("1"), step("2"), step("3", justifiers=["2"])]
        result = audit_argument(steps)
        assert result.satisfied is False
        assert len(result.findings) == 1
        assert result.findings[0].condition == "connectivity"
        assert result.findings[0].step_symbols == ["1"]

    def test_extra_sink_flagged_as_conclusion(self):
        # Step 2 derives from 1 but nothing cites it; step 3 is the final step
        steps = [step("1"), step("2", justifiers=["1"]),
                 step("3", justifiers=["1"])]
        result = audit_argument(steps)
        assert len(result.findings) == 1
        assert result.findings[0].condition == "conclusion"
        assert result.findings[0].step_symbols == ["2"]

    def test_step_not_supporting_final_flagged(self):
        # 1 → 2 chain is cited internally but never reaches the final step 4
        steps = [step("1"), step("2", justifiers=["1"]),
                 step("3"), step("4", justifiers=["3"])]
        result = audit_argument(steps)
        conditions = {f.condition for f in result.findings}
        assert "conclusion" in conditions
        flagged = {sym for f in result.findings for sym in f.step_symbols}
        assert "2" in flagged

    def test_dangling_justifier_flagged_as_integrity(self):
        steps = [step("1"), step("2", justifiers=["1", "99"])]
        result = audit_argument(steps)
        assert any(f.condition == "integrity" and f.step_symbols == ["2"]
                   for f in result.findings)

    def test_self_justification_flagged_as_circular(self):
        steps = [step("1"), step("2", justifiers=["1", "2"])]
        result = audit_argument(steps)
        assert any(f.condition == "circular" and f.step_symbols == ["2"]
                   for f in result.findings)

    def test_cycle_flagged_as_circular(self):
        steps = [step("1", justifiers=["2"]), step("2", justifiers=["1"]),
                 step("3", justifiers=["1"])]
        result = audit_argument(steps)
        cycle = [f for f in result.findings if f.condition == "circular"]
        assert len(cycle) == 1
        assert set(cycle[0].step_symbols) == {"1", "2"}

    def test_dangling_justifier_stays_integrity(self):
        # The dangling-reference check keeps its integrity label after the
        # circular-reasoning findings were split out of integrity.
        steps = [step("1"), step("2", justifiers=["1", "99"])]
        result = audit_argument(steps)
        assert any(f.condition == "integrity" and f.step_symbols == ["2"]
                   for f in result.findings)
        assert not any(f.condition == "circular" for f in result.findings)

    def test_every_finding_has_a_pointer(self):
        steps = [step("1"), step("2"), step("3", justifiers=["2", "99"])]
        result = audit_argument(steps)
        assert result.findings
        assert all(f.pointer for f in result.findings)


class TestAuditEndpoint:
    def test_audit_route(self):
        response = client.post(
            "/api/argument/audit",
            json={
                "argument": [
                    {"symbol": "1", "proposition": "P.", "justifiers": [],
                     "truth_score": ""},
                    {"symbol": "2", "proposition": "Q.",
                     "justifiers": ["1"], "truth_score": ""},
                ],
                "file_ids": [],
            },
        )
        assert response.status_code == 200
        result = response.json()
        assert result["satisfied"] is True
        assert result["findings"] == []

    def test_audit_route_reports_orphan(self):
        response = client.post(
            "/api/argument/audit",
            json={
                "argument": [
                    {"symbol": "1", "proposition": "P.", "justifiers": [],
                     "truth_score": ""},
                    {"symbol": "2", "proposition": "Q.", "justifiers": [],
                     "truth_score": ""},
                    {"symbol": "3", "proposition": "R.",
                     "justifiers": ["2"], "truth_score": ""},
                ],
                "file_ids": [],
            },
        )
        assert response.status_code == 200
        result = response.json()
        assert result["satisfied"] is False
        assert result["findings"][0]["condition"] == "connectivity"
        assert result["findings"][0]["step_symbols"] == ["1"]


class TestAuditCLI:
    def test_cmd_audit(self, tmp_path, capsys):
        from cli.argue import main
        payload = {"argument": [
            {"symbol": "1", "proposition": "P.", "justifiers": [],
             "truth_score": ""},
            {"symbol": "2", "proposition": "Q.", "justifiers": ["1"],
             "truth_score": ""},
        ]}
        path = tmp_path / "argument.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        rc = main(["audit", str(path)])
        assert rc == 0
        out = json.loads(capsys.readouterr().out)
        assert out["satisfied"] is True

    def test_cmd_audit_missing_file(self, tmp_path):
        from cli.argue import main
        rc = main(["audit", str(tmp_path / "nope.json")])
        assert rc == 1
