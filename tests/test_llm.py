import json
import unittest
from unittest import mock

from tutor import llm
from tutor.errors import TutorError
from tutor.llm.answer import parse_answer
from tutor.llm.openrouter import read_completion
from tutor.roleplay import REPLY_SCHEMA, TURN_SCHEMA
from tutor.settings import Settings

REPLY = {"tutor_reply": "Ciao!", "tutor_reply_translation": "Hello!", "conversation_done": False}


class ParseAnswerTest(unittest.TestCase):
    def test_plain_json(self):
        self.assertEqual(parse_answer(json.dumps(REPLY), REPLY_SCHEMA), REPLY)

    def test_json_wrapped_in_a_code_fence_and_prose(self):
        text = f"Here you go:\n```json\n{json.dumps(REPLY)}\n```\nAnything else?"
        self.assertEqual(parse_answer(text, REPLY_SCHEMA), REPLY)

    def test_rejects_what_does_not_match_the_schema(self):
        unreadable = [
            "I would rather chat.",
            "[1, 2, 3]",
            json.dumps({"tutor_reply": "Ciao!"}),                # fields missing
            json.dumps({**REPLY, "tutor_reply": 1}),             # wrong type
            json.dumps({**REPLY, "conversation_done": "no"}),    # wrong type
        ]
        for text in unreadable:
            with self.subTest(text=text), self.assertRaises(TutorError):
                parse_answer(text, REPLY_SCHEMA)

    def test_rejects_a_verdict_outside_the_enum(self):
        turn = {
            "verdict": "splendid", "ideal": "", "alternatives": [], "explanation": "",
            "tutor_reply": "", "tutor_reply_translation": "", "conversation_done": False,
        }
        with self.assertRaises(TutorError):
            parse_answer(json.dumps(turn), TURN_SCHEMA)
        self.assertEqual(parse_answer(json.dumps({**turn, "verdict": "ok"}), TURN_SCHEMA)["verdict"], "ok")


class OpenRouterResponseTest(unittest.TestCase):
    def response(self, **fields) -> bytes:
        return json.dumps(fields).encode()

    def test_content_of_a_normal_answer(self):
        raw = self.response(choices=[{"finish_reason": "stop", "message": {"content": "{}"}}])
        self.assertEqual(read_completion(200, raw), "{}")

    def test_http_errors_become_plain_messages(self):
        for status, expected in [(401, "rejected"), (402, "credit"), (429, "Rate limit"), (500, "(500)")]:
            with self.subTest(status=status), self.assertRaisesRegex(TutorError, expected):
                read_completion(status, b"not json")

    def test_error_inside_a_200_response(self):
        raw = self.response(error={"code": 402, "message": "Insufficient credits"})
        with self.assertRaisesRegex(TutorError, "credit"):
            read_completion(200, raw)
        raw = self.response(error={"code": 503, "message": "Provider overloaded"})
        with self.assertRaisesRegex(TutorError, "Provider overloaded"):
            read_completion(200, raw)

    def test_cut_off_answer(self):
        raw = self.response(choices=[{"finish_reason": "length", "message": {"content": '{"tutor'}}])
        with self.assertRaisesRegex(TutorError, "cut off"):
            read_completion(200, raw)


class AskTest(unittest.TestCase):
    def test_uses_the_chosen_provider_and_checks_the_answer(self):
        claude = mock.Mock(return_value="not json")
        openrouter = mock.Mock(return_value=json.dumps(REPLY))
        with mock.patch.dict(llm.PROVIDERS, {"anthropic": claude, "openrouter": openrouter}):
            settings = Settings(provider="openrouter")
            self.assertEqual(llm.ask(settings, "system", "user", REPLY_SCHEMA), REPLY)
            openrouter.assert_called_once_with(settings, "system", "user", REPLY_SCHEMA)
            claude.assert_not_called()
            with self.assertRaises(TutorError):
                llm.ask(Settings(provider="anthropic"), "system", "user", REPLY_SCHEMA)

    def test_missing_key_is_reported_before_any_request(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            for provider in llm.PROVIDERS:
                with self.subTest(provider=provider), self.assertRaisesRegex(TutorError, "No API key"):
                    llm.ask(Settings(provider=provider), "system", "user", REPLY_SCHEMA)


if __name__ == "__main__":
    unittest.main()
