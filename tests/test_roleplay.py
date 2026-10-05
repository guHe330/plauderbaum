import unittest
from unittest import mock

from tutor import roleplay
from tutor.models import Line, Scenario
from tutor.settings import Settings

BAKERY = Scenario(title="Bakery", brief="The learner buys bread. The tutor plays the baker.")
PATH = [
    Line(role="tutor", text="Buongiorno! Che cosa desidera?"),
    Line(role="learner", text="Vorrei un pane, per favore."),
]


class PromptTest(unittest.TestCase):
    """The model is not called: these check what would be sent to it."""

    def setUp(self):
        patcher = mock.patch.object(roleplay, "ask", return_value={})
        self.ask = patcher.start()
        self.addCleanup(patcher.stop)

    def sent(self) -> tuple[str, str, dict]:
        _settings, system, user, schema = self.ask.call_args.args
        return system, user, schema

    def test_system_prompt_carries_the_settings_and_the_scenario(self):
        settings = Settings(target_language="fr", level="B1", strictness="strict")
        roleplay.open_conversation(settings, BAKERY)
        system, _user, schema = self.sent()
        for expected in ["French tutor", "CEFR level B1", "are in English", "Be strict", "Scenario: Bakery."]:
            self.assertIn(expected, system)
        self.assertIs(schema, roleplay.OPENING_SCHEMA)

    def test_turn_shows_the_path_and_the_new_message(self):
        roleplay.judge_turn(Settings(), BAKERY, "You are at a bakery.", PATH, "il pane integrale")
        _system, user, schema = self.sent()
        self.assertIn("Tutor: Buongiorno! Che cosa desidera?\nLearner: Vorrei un pane, per favore.", user)
        self.assertIn("The learner's new message:\nil pane integrale", user)
        self.assertIs(schema, roleplay.TURN_SCHEMA)

    def test_other_reply_lists_what_was_already_said(self):
        roleplay.other_reply(Settings(), BAKERY, "You are at a bakery.", PATH, ["Certo. Quale pane?", "Subito!"])
        _system, user, schema = self.sent()
        self.assertIn("- Certo. Quale pane?\n- Subito!", user)
        self.assertIn("responding to the learner's last line", user)
        self.assertIs(schema, roleplay.REPLY_SCHEMA)

    def test_other_reply_without_a_path_asks_for_an_opening_line(self):
        roleplay.other_reply(Settings(), BAKERY, "You are at a bakery.", [], ["Buongiorno!"])
        _system, user, _schema = self.sent()
        self.assertIn("has not started yet", user)


class SchemaTest(unittest.TestCase):
    def test_every_field_is_required_and_of_a_checked_type(self):
        from tutor.llm.answer import JSON_TYPES

        for schema in (roleplay.OPENING_SCHEMA, roleplay.TURN_SCHEMA, roleplay.REPLY_SCHEMA):
            self.assertEqual(set(schema["required"]), set(schema["properties"]))
            for spec in schema["properties"].values():
                self.assertIn(spec["type"], JSON_TYPES)


if __name__ == "__main__":
    unittest.main()
