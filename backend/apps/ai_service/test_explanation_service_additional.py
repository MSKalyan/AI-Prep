from apps.ai_service.services.explanation_service import ExplanationService


def test_generate_topic_explanation_builds_prompt_and_returns_llm_text(monkeypatch):
    captured = {}

    class FakeLLM:
        def generate_response(self, prompt):
            captured["prompt"] = prompt
            return "Binary tree explanation"

    monkeypatch.setattr("apps.ai_service.services.explanation_service.LLMService", FakeLLM)

    service = ExplanationService()
    result = service.generate_topic_explanation("Trees", "DSA", 2)

    assert result == "Binary tree explanation"
    assert "Topic: Trees" in captured["prompt"]
    assert "Subject: DSA" in captured["prompt"]
    assert "Week: 2" in captured["prompt"]
    assert "Limit explanation to 3-4 sentences." in captured["prompt"]

