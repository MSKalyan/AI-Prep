from django.test import TestCase
from django.core.files.base import ContentFile
from apps.ai_service.models import Document, Conversation, Message, AIUsageLog
from apps.ai_service.services.rag.llm_service import LLMService
from apps.users.models import User


class DocumentModelTest(TestCase):

    def test_create_document(self):
        document = Document.objects.create(
            title="Test Document",
            content="This is test content",
            document_type="notes",
            subject="CS",
            topic="Arrays",
            exam_type="GATE",
            source_type="upload"
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
            source_type="upload"
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
            source_type="upload"
        )
        self.assertEqual(str(document), "Sample Doc - Mathematics")

    def test_document_chunk_relationship(self):
        parent_doc = Document.objects.create(
            title="Parent",
            content="Parent content",
            document_type="textbook",
            subject="CS",
            exam_type="GATE",
            source_type="upload"
        )
        chunk_doc = Document.objects.create(
            title="Chunk",
            content="Chunk content",
            document_type="notes",
            subject="CS",
            exam_type="GATE",
            source_type="upload",
            parent_document=parent_doc,
            chunk_index=1
        )
        self.assertEqual(chunk_doc.parent_document, parent_doc)
        self.assertIn(chunk_doc, parent_doc.chunks.all())


class ConversationModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='pass'
        )

    def test_create_conversation(self):
        conversation = Conversation.objects.create(
            user=self.user,
            title="Test Chat",
            context="CS Fundamentals"
        )
        self.assertEqual(conversation.user, self.user)
        self.assertEqual(conversation.title, "Test Chat")

    def test_conversation_string_representation(self):
        conversation = Conversation.objects.create(
            user=self.user,
            title="AI Discussion"
        )
        self.assertEqual(str(conversation), "test@example.com - AI Discussion")

    def test_conversation_without_title(self):
        conversation = Conversation.objects.create(user=self.user)
        self.assertEqual(str(conversation), "test@example.com - Conversation")


class MessageModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='pass'
        )
        self.conversation = Conversation.objects.create(
            user=self.user,
            title="Test Chat"
        )

    def test_create_message(self):
        message = Message.objects.create(
            conversation=self.conversation,
            role="user",
            content="Hello AI",
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30
        )
        self.assertEqual(message.role, "user")
        self.assertEqual(message.content, "Hello AI")
        self.assertEqual(message.total_tokens, 30)

    def test_message_string_representation(self):
        message = Message.objects.create(
            conversation=self.conversation,
            role="assistant",
            content="Hello! How can I help you today?"
        )
        self.assertEqual(str(message), "assistant: Hello! How can I help you today?...")


class AIUsageLogModelTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='pass'
        )

    def test_create_usage_log(self):
        log = AIUsageLog.objects.create(
            user=self.user,
            endpoint="topic-explanation",
            model_used="llama-3.1-8b-instant",
            prompt_tokens=100,
            completion_tokens=200,
            total_tokens=300,
            cost=0.001,
            success=True,
            response_time_ms=1500
        )
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.endpoint, "topic-explanation")
        self.assertEqual(log.total_tokens, 300)
        self.assertTrue(log.success)

    def test_usage_log_with_error(self):
        log = AIUsageLog.objects.create(
            user=self.user,
            endpoint="generate-questions",
            model_used="gpt-4",
            success=False,
            error_message="API key invalid"
        )
        self.assertFalse(log.success)
        self.assertEqual(log.error_message, "API key invalid")

    def test_usage_log_string_representation(self):
        log = AIUsageLog.objects.create(
            user=self.user,
            endpoint="ask-ai",
            model_used="llama-3.1-8b-instant",
            total_tokens=150
        )
        self.assertEqual(str(log), "test@example.com - ask-ai - 150 tokens")


class LLMServiceTest(TestCase):

    def test_generate_response_safe(self):
        service = LLMService()
        result = service.generate_response("Explain arrays")
        # Should NOT crash even if API key missing
        self.assertTrue(result is None or isinstance(result, str))