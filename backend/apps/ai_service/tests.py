from django.test import TestCase
from django.core.files.base import ContentFile
from django.conf import settings
from rest_framework.test import APIClient

from apps.ai_service.models import Document, Conversation, Message, AIUsageLog
from apps.ai_service.services.llm_service import LLMService
from apps.ai_service.serializers import (
    AskAISerializer,
    GenerateQuestionsAISerializer,
    DocumentUploadSerializer,
    ConversationSerializer,
)
from apps.users.models import User
from apps.ai_service.serializers import (
    AskAISerializer,
    GenerateQuestionsAISerializer,
    DocumentUploadSerializer,
    ConversationSerializer,
)

TEST_PASSWORD = getattr(settings, "TEST_PASSWORD", "testpass123!@#")
TEST_EMAIL = "test@example.com"


class TestDocumentModel(TestCase):
    def test_create_document(self):
        document = Document.objects.create(
            title="Test Document",
            content="This is test content",
            document_type="notes",
            subject="CS",
            topic="Arrays",
            exam_type="GATE",
            source_type="upload",
        )
        self.assertEqual(document.title, "Test Document")
        self.assertEqual(document.content, "This is test content")
        self.assertEqual(document.document_type, "notes")

    def test_document_with_file(self):
        file_content = b"Test file content"
        document = Document.objects.create(
            title="File Document",
            content="Content",
            document_type="notes",
            subject="CS",
            exam_type="GATE",
            source_type="upload",
        )
        document.file.save("test.txt", ContentFile(file_content))
        self.assertIsNotNone(document.file)

    def test_document_string_representation(self):
        document = Document.objects.create(
            title="Sample Doc",
            content="Content",
            document_type="notes",
            subject="Mathematics",
            exam_type="GATE",
            source_type="upload",
        )
        self.assertEqual(str(document), "Sample Doc - Mathematics")

    def test_document_default_values(self):
        document = Document.objects.create(
            title="Default Doc", content="Content", subject="CS", exam_type="GATE"
        )
        self.assertEqual(document.document_type, "notes")
        self.assertEqual(document.source_type, "upload")
        self.assertFalse(document.processed)
        self.assertEqual(document.tags, [])

    def test_document_with_json_fields(self):
        document = Document.objects.create(
            title="JSON Doc",
            content="Content",
            subject="CS",
            exam_type="GATE",
            tags=["tag1", "tag2"],
        )
        self.assertEqual(document.tags, ["tag1", "tag2"])


class TestConversationModel(TestCase):
    def test_create_conversation(self):
        user = User.objects.create_user(email=TEST_EMAIL, password=TEST_PASSWORD)
        conversation = Conversation.objects.create(
            user=user, title="Test Chat", context="CS Fundamentals"
        )
        self.assertEqual(conversation.user, user)
        self.assertEqual(conversation.title, "Test Chat")

    def test_conversation_string_representation(self):
        user = User.objects.create_user(email=TEST_EMAIL, password=TEST_PASSWORD)
        conversation = Conversation.objects.create(user=user, title="AI Discussion")
        self.assertEqual(str(conversation), "test@example.com - AI Discussion")

    def test_conversation_without_title(self):
        user = User.objects.create_user(email=TEST_EMAIL, password=TEST_PASSWORD)
        conversation = Conversation.objects.create(user=user)
        self.assertEqual(str(conversation), "test@example.com - Conversation")

    def test_conversation_default_values(self):
        user = User.objects.create_user(email=TEST_EMAIL, password=TEST_PASSWORD)
        conversation = Conversation.objects.create(user=user)
        self.assertEqual(conversation.title, "")
        self.assertEqual(conversation.context, "")


class TestMessageModel(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=TEST_EMAIL, password=TEST_PASSWORD)
        self.conversation = Conversation.objects.create(
            user=self.user, title="Test Chat"
        )

    def test_create_message(self):
        message = Message.objects.create(
            conversation=self.conversation,
            role="user",
            content="Hello AI",
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30,
        )
        self.assertEqual(message.role, "user")
        self.assertEqual(message.total_tokens, 30)

    def test_message_string_representation(self):
        message = Message.objects.create(
            conversation=self.conversation,
            role="assistant",
            content="Hello! How can I help you today?",
        )
        self.assertTrue(str(message).startswith("assistant:"))

    def test_message_default_values(self):
        message = Message.objects.create(
            conversation=self.conversation, role="user", content="Test"
        )
        self.assertEqual(message.prompt_tokens, 0)
        self.assertEqual(message.total_tokens, 0)
        self.assertEqual(message.retrieved_documents, [])
        self.assertIsNone(message.confidence_score)


class TestAIUsageLogModel(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(email=TEST_EMAIL, password=TEST_PASSWORD)

    def test_create_usage_log(self):
        log = AIUsageLog.objects.create(
            user=self.user,
            endpoint="topic-explanation",
            model_used="llama",
            total_tokens=300,
        )
        self.assertEqual(log.user, self.user)

    def test_usage_log_default_values(self):
        log = AIUsageLog.objects.create(
            user=self.user, endpoint="test", model_used="test-model"
        )
        self.assertEqual(log.total_tokens, 0)
        self.assertTrue(log.success)

    def test_usage_log_with_error(self):
        log = AIUsageLog.objects.create(
            user=self.user,
            endpoint="test",
            model_used="test-model",
            success=False,
            error_message="Something went wrong",
            response_time_ms=1500,
        )
        self.assertFalse(log.success)
        self.assertEqual(log.error_message, "Something went wrong")
        self.assertEqual(log.response_time_ms, 1500)


class TestLLMService(TestCase):
    def test_generate_response_safe(self):
        service = LLMService()
        result = service.generate_response("Explain arrays")
        self.assertTrue(result is None or isinstance(result, str))


class TestAskAISerializer(TestCase):
    def test_valid_ask_ai_data(self):
        serializer = AskAISerializer(
            data={
                "question": "What are arrays?",
                "context": "Data Structures",
                "exam_type": "GATE",
            }
        )
        self.assertTrue(serializer.is_valid())

    def test_ask_ai_question_required(self):
        serializer = AskAISerializer(data={"context": "CS"})
        self.assertFalse(serializer.is_valid())
        self.assertIn("question", serializer.errors)

    def test_ask_ai_question_max_length(self):
        serializer = AskAISerializer(data={"question": "x" * 3000})
        self.assertFalse(serializer.is_valid())

    def test_ask_ai_optional_fields(self):
        serializer = AskAISerializer(data={"question": "Test question"})
        self.assertTrue(serializer.is_valid())


class TestGenerateQuestionsAISerializer(TestCase):
    def test_valid_generate_questions(self):
        serializer = GenerateQuestionsAISerializer(
            data={
                "exam_type": "GATE",
                "subject": "Computer Science",
                "difficulty": "medium",
                "num_questions": 5,
                "question_type": "mcq",
            }
        )
        self.assertTrue(serializer.is_valid())

    def test_generate_questions_invalid_difficulty(self):
        serializer = GenerateQuestionsAISerializer(
            data={
                "exam_type": "GATE",
                "subject": "CS",
                "difficulty": "invalid",
                "num_questions": 5,
                "question_type": "mcq",
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("difficulty", serializer.errors)

    def test_generate_questions_num_questions_range(self):
        serializer = GenerateQuestionsAISerializer(
            data={
                "exam_type": "GATE",
                "subject": "CS",
                "difficulty": "easy",
                "num_questions": 25,
                "question_type": "mcq",
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("num_questions", serializer.errors)

    def test_generate_questions_question_type_choices(self):
        serializer = GenerateQuestionsAISerializer(
            data={
                "exam_type": "GATE",
                "subject": "CS",
                "difficulty": "easy",
                "num_questions": 5,
                "question_type": "invalid_type",
            }
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("question_type", serializer.errors)


class TestDocumentUploadSerializer(TestCase):
    def test_valid_document_upload(self):
        user = User.objects.create_user(email=TEST_EMAIL, password=TEST_PASSWORD)
        from unittest.mock import MagicMock

        request = MagicMock()
        request.user = user
        serializer = DocumentUploadSerializer(
            data={
                "title": "Test Doc",
                "subject": "CS",
                "exam_type": "GATE",
            },
            context={"request": request},
        )
        self.assertTrue(serializer.is_valid())


class TestConversationSerializer(TestCase):
    def test_serialize_conversation(self):
        user = User.objects.create_user(email=TEST_EMAIL, password=TEST_PASSWORD)
        conversation = Conversation.objects.create(
            user=user, title="Test Chat", context="CS"
        )
        Message.objects.create(conversation=conversation, role="user", content="Hello")
        serializer = ConversationSerializer(conversation)
        self.assertEqual(serializer.data["title"], "Test Chat")
        self.assertEqual(serializer.data["context"], "CS")
        self.assertEqual(serializer.data["message_count"], 1)


class TestAskAIView(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email=TEST_EMAIL, password=TEST_PASSWORD)

    def test_unauthenticated(self):
        response = self.client.post("/api/ask-ai/", {}, format="json")
        self.assertEqual(response.status_code, 401)

    def test_authenticated_get(self):
        Conversation.objects.create(user=self.user, title="Chat")
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/ask-ai/")
        self.assertEqual(response.status_code, 200)

    def test_authenticated_post_invalid_data(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post("/api/ask-ai/", {}, format="json")
        self.assertEqual(response.status_code, 400)


class TestGenerateQuestionsView(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email=TEST_EMAIL, password=TEST_PASSWORD)

    def test_generate_questions_unauthenticated(self):
        response = self.client.post("/api/generate-questions/", {}, format="json")
        self.assertEqual(response.status_code, 401)

    def test_generate_questions_invalid_data(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post("/api/generate-questions/", {}, format="json")
        self.assertEqual(response.status_code, 400)


class TestDocumentUploadView(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email=TEST_EMAIL, password=TEST_PASSWORD)

    def test_upload_document_unauthenticated(self):
        response = self.client.post("/api/documents/", {}, format="json")
        self.assertEqual(response.status_code, 401)

    def test_upload_document_missing_fields(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post("/api/documents/", {"title": "Test"})
        self.assertEqual(response.status_code, 400)


class TestProcessDocumentView(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email=TEST_EMAIL, password=TEST_PASSWORD)

    def test_process_document_not_found(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            "/api/documents/process/", {"document_id": 9999}, format="json"
        )
        self.assertEqual(response.status_code, 404)

    def test_process_document_missing_id(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post("/api/documents/process/", {}, format="json")
        self.assertEqual(response.status_code, 400)


class TestConversationMessagesView(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email=TEST_EMAIL, password=TEST_PASSWORD)
        self.other_user = User.objects.create_user(
            email="other@example.com", password=TEST_PASSWORD
        )

        self.conversation = Conversation.objects.create(
            user=self.user, title="Test Chat"
        )

    def test_requires_auth(self):
        response = self.client.get(
            f"/api/conversations/{self.conversation.id}/messages/"
        )
        self.assertEqual(response.status_code, 401)

    def test_returns_messages_in_order(self):
        Message.objects.create(
            conversation=self.conversation, role="user", content="Hi"
        )
        Message.objects.create(
            conversation=self.conversation, role="assistant", content="Hello"
        )

        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            f"/api/conversations/{self.conversation.id}/messages/"
        )
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["content"], "Hi")
        self.assertEqual(data[1]["content"], "Hello")

    def test_cannot_access_other_users_conversation(self):
        other_convo = Conversation.objects.create(user=self.other_user, title="Other")
        Message.objects.create(conversation=other_convo, role="user", content="Secret")

        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"/api/conversations/{other_convo.id}/messages/")
        self.assertEqual(response.status_code, 404)

    def test_messages_limit_param(self):
        for i in range(15):
            Message.objects.create(
                conversation=self.conversation, role="user", content=f"Message {i}"
            )

        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            f"/api/conversations/{self.conversation.id}/messages/?limit=5"
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 5)


class TestHealthCheckView(TestCase):
    def test_health(self):
        client = APIClient()
        response = client.get("/api/health/")
        self.assertEqual(response.status_code, 200)


class TestAskAIViewErrorHandling(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email=TEST_EMAIL, password=TEST_PASSWORD)

    def test_ask_ai_conversation_not_found(self):
        from unittest.mock import patch
        self.client.force_authenticate(user=self.user)
        with patch("apps.ai_service.services.services.AIService.ask_ai") as mock_ask:
            mock_ask.side_effect = Conversation.DoesNotExist("Conversation not found")
            response = self.client.post(
                "/api/ask-ai/",
                {"question": "test", "conversation_id": 99999},
                format="json"
            )
            self.assertEqual(response.status_code, 404)

    def test_ask_ai_generic_exception(self):
        from unittest.mock import patch
        self.client.force_authenticate(user=self.user)
        with patch("apps.ai_service.services.services.AIService.ask_ai") as mock_ask:
            mock_ask.side_effect = Exception("Some error")
            response = self.client.post(
                "/api/ask-ai/",
                {"question": "test"},
                format="json"
            )
            self.assertEqual(response.status_code, 500)


class TestConversationMessagesViewErrorHandling(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email=TEST_EMAIL, password=TEST_PASSWORD)
        self.conversation = Conversation.objects.create(user=self.user, title="Test")

    def test_conversation_not_found(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get("/api/conversations/99999/messages/")
        self.assertEqual(response.status_code, 404)

    def test_invalid_limit_param(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(f"/api/conversations/{self.conversation.id}/messages/?limit=abc")
        self.assertEqual(response.status_code, 200)


class TestProcessDocumentViewErrorHandling(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email=TEST_EMAIL, password=TEST_PASSWORD)

    def test_process_document_not_found(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            "/api/documents/process/",
            {"document_id": 99999},
            format="json"
        )
        self.assertEqual(response.status_code, 404)

    def test_process_document_already_processed(self):
        from apps.ai_service.models import Document
        doc = Document.objects.create(user=self.user, title="Test", processed=True)
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            "/api/documents/process/",
            {"document_id": doc.id},
            format="json"
        )
        self.assertEqual(response.status_code, 200)

    def test_process_document_generic_error(self):
        from unittest.mock import patch
        from apps.ai_service.models import Document
        doc = Document.objects.create(user=self.user, title="Test", processed=False)
        self.client.force_authenticate(user=self.user)
        with patch("apps.ai_service.views.RAGService.ingest_document") as mock_ingest:
            mock_ingest.side_effect = Exception("RAG error")
            response = self.client.post(
                "/api/documents/process/",
                {"document_id": doc.id},
                format="json"
            )
            self.assertEqual(response.status_code, 500)


class TestAISerializers(TestCase):
    def test_ask_ai_serializer_valid(self):
        data = {"question": "What is an array?", "context": "Data Structures"}
        serializer = AskAISerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_ask_ai_serializer_missing_question(self):
        data = {"context": "Data Structures"}
        serializer = AskAISerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("question", serializer.errors)

    def test_ask_ai_serializer_question_too_long(self):
        data = {"question": "x" * 3000}
        serializer = AskAISerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_ask_ai_serializer_with_exam_type(self):
        data = {"question": "What is GATE?", "exam_type": "GATE CS"}
        serializer = AskAISerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_ask_ai_serializer_with_conversation_id(self):
        data = {"question": "Continue", "conversation_id": 123}
        serializer = AskAISerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_generate_questions_serializer_valid(self):
        data = {
            "exam_type": "GATE",
            "subject": "Computer Science",
            "difficulty": "easy",
            "num_questions": 5,
            "question_type": "mcq",
        }
        serializer = GenerateQuestionsAISerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_generate_questions_serializer_invalid_difficulty(self):
        data = {
            "exam_type": "GATE",
            "subject": "CS",
            "difficulty": "invalid",
            "num_questions": 5,
            "question_type": "mcq",
        }
        serializer = GenerateQuestionsAISerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_generate_questions_serializer_num_questions_min(self):
        data = {
            "exam_type": "GATE",
            "subject": "CS",
            "difficulty": "easy",
            "num_questions": 0,
            "question_type": "mcq",
        }
        serializer = GenerateQuestionsAISerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_generate_questions_serializer_num_questions_max(self):
        data = {
            "exam_type": "GATE",
            "subject": "CS",
            "difficulty": "easy",
            "num_questions": 25,
            "question_type": "mcq",
        }
        serializer = GenerateQuestionsAISerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_generate_questions_serializer_with_topic(self):
        data = {
            "exam_type": "GATE",
            "subject": "CS",
            "topic": "Arrays",
            "difficulty": "easy",
            "num_questions": 5,
            "question_type": "mcq",
        }
        serializer = GenerateQuestionsAISerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_roadmap_ai_response_serializer_valid(self):
        from apps.ai_service.serializers import RoadmapAIResponseSerializer

        original = {
            "weeks": [
                {"week": 1, "phase": "study", "topics": [{"name": "Arrays", "hours": 2}]}
            ]
        }
        data = {
            "weeks": [
                {"week": 1, "phase": "study", "topics": [{"name": "Arrays", "hours": 2, "explanation": "test"}]}
            ]
        }
        serializer = RoadmapAIResponseSerializer(data=data, context={"original": original})
        self.assertTrue(serializer.is_valid())

    def test_roadmap_ai_response_serializer_week_count_mismatch(self):
        from apps.ai_service.serializers import RoadmapAIResponseSerializer

        original = {"weeks": [{"week": 1, "phase": "study", "topics": [{"name": "Arrays", "hours": 2}]}]}
        data = {"weeks": []}
        serializer = RoadmapAIResponseSerializer(data=data, context={"original": original})
        self.assertFalse(serializer.is_valid())
