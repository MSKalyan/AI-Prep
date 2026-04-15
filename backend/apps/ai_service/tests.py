from django.test import TestCase
from django.core.files.base import ContentFile
from django.conf import settings
from rest_framework.test import APIClient

from apps.ai_service.models import Document, Conversation, Message, AIUsageLog
from apps.users.models import User
from apps.ai_service.services.llm_service import LLMService

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


class TestLLMService(TestCase):
    def test_generate_response_safe(self):
        service = LLMService()
        result = service.generate_response("Explain arrays")
        self.assertTrue(result is None or isinstance(result, str))


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


class TestHealthCheckView(TestCase):
    def test_health(self):
        client = APIClient()
        response = client.get("/api/health/")
        self.assertEqual(response.status_code, 200)
