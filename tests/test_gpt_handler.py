import unittest

from handlers.gpt_handler import (
    WEB_SEARCH_TOOL,
    WEB_SEARCH_TOOL_CHOICE,
    build_response_create_kwargs,
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


if __name__ == "__main__":
    unittest.main()
