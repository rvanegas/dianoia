"""Extraction with a conversation's participants: each step says who accepts
and who rejects it, by the names given and no others."""

import json
from unittest.mock import patch

from services import extraction


def _extract(reply: dict, **kwargs):
    seen = {}

    def call(self, prompt, file_ids):
        seen["instructions"], seen["schema"] = self.instructions, self.response_format_base
        return json.dumps(reply)

    with patch.object(extraction.ModelAgent, "call", call):
        return extraction.extract_argument("Ann: p. Bob: not p.", **kwargs), seen


def test_participants_are_asked_for_their_stances_and_kept_to_the_names_given():
    reply = {"argument": [
        {"symbol": "1", "proposition": "P.", "justifiers": [], "truth_score": "",
         "accepted": ["Ann", "Ann", "Zed"], "rejected": ["Bob", "Ann"]},
        {"symbol": "2", "proposition": "Q.", "justifiers": ["1"], "truth_score": "",
         "accepted": [], "rejected": []},
    ]}
    result, seen = _extract(reply, participants=["Ann", "Bob"])
    assert [(s["accepted"], s["rejected"]) for s in result["argument"]] == [(["Ann"], ["Bob"]), ([], [])]
    assert "participants: Ann, Bob" in seen["instructions"]
    step = seen["schema"]["properties"]["argument"]["items"]
    assert step["properties"]["accepted"]["items"]["enum"] == ["Ann", "Bob"]
    assert {"accepted", "rejected"} <= set(step["required"])


def test_without_participants_extraction_is_as_it_was():
    reply = {"argument": [{"symbol": "1", "proposition": "P.", "justifiers": [], "truth_score": ""}]}
    result, seen = _extract(reply)
    assert result == reply
    assert seen["instructions"] == extraction._EXTRACTION_SYSTEM_PROMPT
    assert seen["schema"] is extraction._RESPONSE_FORMAT
