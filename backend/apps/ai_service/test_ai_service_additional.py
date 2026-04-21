from types import SimpleNamespace

import pytest

from apps.ai_service.services.services import AIService


class _MsgList(list):
    def order_by(self, *_args, **_kwargs):
        return self


class _MsgManager:
    def __init__(self, msgs):
        self._msgs = _MsgList(msgs)

    def all(self):
        return self._msgs


def _mk_conversation(cid=1, msgs=None):
    return SimpleNamespace(id=cid, messages=_MsgManager(msgs or []))


def _mk_ai_service(monkeypatch, ai_mode="mock"):
    monkeypatch.setenv("AI_MODE", ai_mode)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setattr("apps.ai_service.services.services.RAGService", lambda: SimpleNamespace(query=lambda **_k: {}))
    return AIService()


def test_should_fallback_parametrized(monkeypatch):
    svc = _mk_ai_service(monkeypatch)
    assert svc._should_fallback("") is True
    assert svc._should_fallback("No relevant information found in docs") is True
    assert svc._should_fallback("short text") is True
    assert svc._should_fallback("This is a long useful answer that is definitely above fifty characters.") is False


def test_build_prompts_include_context_and_modes(monkeypatch):
    svc = _mk_ai_service(monkeypatch)
    strict = svc._build_system_prompt("OS", "GATE", strict=True)
    loose = svc._build_system_prompt("OS", "GATE", strict=False)
    assert "strict exam assistant" in strict.lower()
    assert "helpful exam assistant" in loose.lower()
    assert "Context hint: OS" in strict
    assert "Exam: GATE" in strict

    p1 = svc._build_prompt("What is OS?", "ctx", strict=True)
    p2 = svc._build_prompt("What is OS?", "ctx", strict=False)
    p3 = svc._build_prompt("What is OS?", "", strict=False)
    assert "Answer ONLY from the context" in p1
    assert "general knowledge" in p2
    assert "Context:" in p2
    assert "Context:" not in p3


def test_build_messages_keeps_history_order(monkeypatch):
    svc = _mk_ai_service(monkeypatch)
    prev = [SimpleNamespace(role="user", content="u1"), SimpleNamespace(role="assistant", content="a1")]
    msgs = svc._build_messages("sys", "usr", prev)
    assert msgs[0]["role"] == "system"
    assert msgs[1]["content"] == "u1"
    assert msgs[2]["content"] == "a1"
    assert msgs[3]["role"] == "user"


def test_call_llm_mock_mode(monkeypatch):
    svc = _mk_ai_service(monkeypatch, ai_mode="mock")
    resp = svc._call_llm([{"role": "user", "content": "hi"}])
    assert resp["choices"][0]["message"]["content"] == "Mock response"
    assert resp["usage"]["total_tokens"] == 0


def test_call_llm_groq_mode(monkeypatch):
    monkeypatch.setenv("AI_MODE", "groq")
    monkeypatch.setenv("GROQ_API_KEY", "k")
    monkeypatch.setattr("apps.ai_service.services.services.RAGService", lambda: SimpleNamespace(query=lambda **_k: {}))

    usage = SimpleNamespace(prompt_tokens=3, completion_tokens=4, total_tokens=7)
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="from groq"))],
        usage=usage,
    )
    fake_client = SimpleNamespace(
        chat=SimpleNamespace(completions=SimpleNamespace(create=lambda **_k: response))
    )
    monkeypatch.setattr("apps.ai_service.services.services.Groq", lambda **_k: fake_client)
    svc = AIService()
    resp = svc._call_llm([{"role": "user", "content": "hi"}])
    assert resp["choices"][0]["message"]["content"] == "from groq"
    assert resp["usage"]["total_tokens"] == 7


def test_call_llm_gemini_mode(monkeypatch):
    monkeypatch.setenv("AI_MODE", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "k")
    monkeypatch.setattr("apps.ai_service.services.services.RAGService", lambda: SimpleNamespace(query=lambda **_k: {}))
    fake_genai = SimpleNamespace(
        configure=lambda **_k: None,
        GenerativeModel=lambda *_a, **_k: SimpleNamespace(
            generate_content=lambda _p: SimpleNamespace(text="from gemini")
        ),
    )
    monkeypatch.setattr("apps.ai_service.services.services.genai", fake_genai)
    svc = AIService()
    resp = svc._call_llm([{"role": "user", "content": "hi"}])
    assert resp["choices"][0]["message"]["content"] == "from gemini"


def test_call_llm_invalid_mode_raises(monkeypatch):
    svc = _mk_ai_service(monkeypatch)
    svc.ai_mode = "invalid"
    with pytest.raises(ValueError, match="Invalid AI_MODE"):
        svc._call_llm([])


def test_call_with_context_and_fallback_uses_fallback_when_needed(monkeypatch):
    svc = _mk_ai_service(monkeypatch)
    monkeypatch.setattr(svc, "_call_with_prompt", lambda *_a, **_k: ("Not found", {"total_tokens": 1}))
    monkeypatch.setattr(svc, "_call_with_fallback", lambda *_a, **_k: ("Fallback answer", {"total_tokens": 2}))
    answer, usage = svc._call_with_context_and_fallback(["d1", "d2"], "q", [], "c", "e")
    assert answer == "Fallback answer"
    assert usage["total_tokens"] == 2


def test_ask_ai_clarification_short_circuit(monkeypatch):
    svc = _mk_ai_service(monkeypatch)
    out = svc.ask_ai(user=object(), question="ok")
    assert out["mode"] == "clarification"
    assert out["confidence"] == 0


def test_ask_ai_no_docs_path_creates_conversation_and_messages(monkeypatch):
    svc = _mk_ai_service(monkeypatch)
    conv = _mk_conversation(cid=9, msgs=[SimpleNamespace(role="user", content="old")])

    class _Manager:
        def get(self, **_kwargs):
            raise DoesNotExist

        def create(self, **_kwargs):
            return conv

    class DoesNotExist(Exception):
        pass

    created_messages = []
    monkeypatch.setattr("apps.ai_service.services.services.Conversation", SimpleNamespace(objects=_Manager(), DoesNotExist=DoesNotExist))
    monkeypatch.setattr(
        "apps.ai_service.services.services.Message",
        SimpleNamespace(objects=SimpleNamespace(create=lambda **kwargs: created_messages.append(kwargs))),
    )
    usage_logs = []
    monkeypatch.setattr(
        "apps.ai_service.services.services.AIUsageLog",
        SimpleNamespace(objects=SimpleNamespace(create=lambda **kwargs: usage_logs.append(kwargs))),
    )
    svc.rag = SimpleNamespace(query=lambda **_kwargs: {"documents": [], "answer": ""})
    monkeypatch.setattr(svc, "_call_with_fallback", lambda *_a, **_k: ("fallback", {"total_tokens": 11}))

    out = svc.ask_ai(user=object(), question="What is OS?", context="OS", conversation_id=1, exam_type="GATE")
    assert out["answer"] == "fallback"
    assert out["confidence"] == 0.5
    assert out["conversation_id"] == 9
    assert len(created_messages) == 2
    assert usage_logs[-1]["success"] is True


def test_ask_ai_docs_found_no_fallback(monkeypatch):
    svc = _mk_ai_service(monkeypatch)
    conv = _mk_conversation(cid=5)

    monkeypatch.setattr(
        "apps.ai_service.services.services.Conversation",
        SimpleNamespace(objects=SimpleNamespace(create=lambda **_k: conv)),
    )
    monkeypatch.setattr(
        "apps.ai_service.services.services.Message",
        SimpleNamespace(objects=SimpleNamespace(create=lambda **_k: None)),
    )
    monkeypatch.setattr(
        "apps.ai_service.services.services.AIUsageLog",
        SimpleNamespace(objects=SimpleNamespace(create=lambda **_k: None)),
    )
    svc.rag = SimpleNamespace(query=lambda **_kwargs: {"documents": ["d1", "d2", "d3", "d4"], "answer": "x" * 60})
    out = svc.ask_ai(user=object(), question="Explain", context="", exam_type="")
    assert out["confidence"] == 1.0
    assert len(out["sources"]) == 3


def test_ask_ai_exception_logs_and_reraises(monkeypatch):
    svc = _mk_ai_service(monkeypatch)
    monkeypatch.setattr(svc, "_log_usage", lambda **kwargs: kwargs)
    svc.rag = SimpleNamespace(query=lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("boom")))
    monkeypatch.setattr(
        "apps.ai_service.services.services.Conversation",
        SimpleNamespace(objects=SimpleNamespace(create=lambda **_k: _mk_conversation(cid=3))),
    )
    with pytest.raises(RuntimeError, match="boom"):
        svc.ask_ai(user=object(), question="x")


def test_log_usage_ignores_internal_create_errors(monkeypatch):
    svc = _mk_ai_service(monkeypatch)
    monkeypatch.setattr(
        "apps.ai_service.services.services.AIUsageLog",
        SimpleNamespace(objects=SimpleNamespace(create=lambda **_k: (_ for _ in ()).throw(Exception("db")))),
    )
    svc._log_usage(
        user=object(),
        endpoint="ask-ai",
        usage={},
        response_time=1,
        success=False,
        error_message="e",
    )
