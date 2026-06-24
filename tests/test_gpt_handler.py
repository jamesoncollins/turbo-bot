import unittest
from unittest.mock import patch

from handlers.gpt_handler import (
    DEFAULT_IMAGE_MODEL,
    WEB_SEARCH_TOOL,
    WEB_SEARCH_TOOL_CHOICE,
    GptHandler,
    build_response_create_kwargs,
    is_image_model,
    should_force_web_search,
)


class GptHandlerWebSearchTest(unittest.TestCase):
    def test_should_force_web_search_for_time_sensitive_queries(self):
        prompts = [
            "what is the latest news about OpenAI?",
            "weather in Chicago today",
            "Who is the CEO of Microsoft?",
            "compare the best phones in 2026",
            "summarize https://example.com/article",
        ]

        for prompt in prompts:
            with self.subTest(prompt=prompt):
                self.assertTrue(should_force_web_search(prompt))

    def test_should_not_force_web_search_for_clearly_timeless_requests(self):
        prompts = [
            "write a birthday toast for my friend",
            "explain recursion with a simple analogy",
            "give me three names for a fantasy tavern",
        ]

        for prompt in prompts:
            with self.subTest(prompt=prompt):
                self.assertFalse(should_force_web_search(prompt))

    def test_build_response_kwargs_requires_web_search_when_forced(self):
        kwargs = build_response_create_kwargs(
            model="gpt-4.1",
            tools=[WEB_SEARCH_TOOL],
            input_data=[{"role": "user", "content": "weather today"}],
            force_web_search=True,
        )

        self.assertEqual(kwargs["tool_choice"], WEB_SEARCH_TOOL_CHOICE)
        self.assertEqual(kwargs["tools"], [WEB_SEARCH_TOOL])
        self.assertEqual(kwargs["include"], ["web_search_call.action.sources"])

    def test_build_response_kwargs_omits_tool_choice_by_default(self):
        kwargs = build_response_create_kwargs(
            model="gpt-4.1",
            tools=[WEB_SEARCH_TOOL],
            input_data=[{"role": "user", "content": "write a poem"}],
        )

        self.assertNotIn("tool_choice", kwargs)


class GptHandlerImageModelTest(unittest.TestCase):
    def test_default_image_model_uses_current_accessible_gpt_image_model(self):
        self.assertEqual(DEFAULT_IMAGE_MODEL, "gpt-image-1-mini")
        self.assertTrue(is_image_model(DEFAULT_IMAGE_MODEL))

    def test_image_alias_resolves_to_default_image_model(self):
        handler = GptHandler("#gpt.image draw a tiny robot")
        self.assertTrue(handler.can_handle())

        with patch("handlers.gpt_handler.submit_gpt_image_gen") as submit_mock:
            submit_mock.return_value = {"message": "ok", "attachments": []}

            response = handler.process_message("#gpt.image draw a tiny robot", None)

        self.assertEqual(response, {"message": "ok", "attachments": []})
        submit_mock.assert_called_once_with("draw a tiny robot", None, DEFAULT_IMAGE_MODEL)

    def test_image_generation_returns_fallback_message_without_revised_prompt(self):
        class ImageData:
            b64_json = "abc123"
            revised_prompt = None

        class Response:
            data = [ImageData()]

        handler = GptHandler("#gpt.image draw a tiny robot")
        self.assertTrue(handler.can_handle())

        with patch("handlers.gpt_handler.client.images.generate", return_value=Response()):
            response = handler.process_message("#gpt.image draw a tiny robot", None)

        self.assertEqual(response, {"message": "Generated image attached.", "attachments": ["abc123"]})

    def test_image_generation_session_key_returns_dict(self):
        from handlers.gpt_handler import submit_gpt_image_gen

        response = submit_gpt_image_gen("draw a tiny robot", session_key="chat")

        self.assertEqual(
            response,
            {"message": "Image generation does not use conversation history.", "attachments": []},
        )


if __name__ == "__main__":
    unittest.main()
