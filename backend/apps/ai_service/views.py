import traceback
from django.http import JsonResponse
from .models import Message
from apps.ai_service.services.rag.scrape_document import scrape_and_store_document
from apps.ai_service.services.rag.text_extractor import extract_text
from apps.ai_service.services.rag.document_cleaner import clean_document
from apps.ai_service.services.rag.document_chunker import create_chunks
from apps.ai_service.services.rag.document_pipeline import process_document
from apps.ai_service.services.rag.embed_chunks import embed_document_chunks
from .services.rag.vector_search import semantic_search
from .services.rag.rag_service import RAGService
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser
from .serializers import (
    AskAISerializer,
    DocumentUploadSerializer,
    DocumentUploadSerializer,
    GenerateQuestionsAISerializer,
    ConversationSerializer,
    MessageSerializer
)
from .services.rag.chat_service import AIService
from .models import Conversation, Document


class AskAIView(APIView):

    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = AskAISerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                ai_service = AIService()
                
                result = ai_service.ask_ai(
                    user=request.user,
                    question=serializer.validated_data['question'],
                    context=serializer.validated_data.get('context', ''),
                    conversation_id=serializer.validated_data.get('conversation_id'),
                    exam_type=serializer.validated_data.get('exam_type', '')
                )
                
                return Response(result, status=status.HTTP_200_OK)
            
            except Conversation.DoesNotExist:
                return Response(
                    {'error': 'Conversation not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            except Exception as e:
                traceback.print_exc()
                return Response(
                    {'error': f'AI service error: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request):
        conversations = Conversation.objects.filter(user=request.user)[:20]
        serializer = ConversationSerializer(conversations, many=True)
        return Response(serializer.data)




    def get_messages(request, conversation_id):
        messages = Message.objects.filter(
            conversation_id=conversation_id
        ).order_by('-created_at')[:10]

        messages = list(messages)[::-1]

        return JsonResponse([
            {
                "role": m.role,
                "content": m.content,
                "retrieved_documents": m.retrieved_documents
            }
            for m in messages
        ], safe=False)

class GenerateQuestionsView(APIView):

    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = GenerateQuestionsAISerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                ai_service = AIService()
                
                questions = ai_service.generate_questions(
                    exam_type=serializer.validated_data['exam_type'],
                    subject=serializer.validated_data['subject'],
                    topic=serializer.validated_data.get('topic', ''),
                    difficulty=serializer.validated_data['difficulty'],
                    num_questions=serializer.validated_data['num_questions'],
                    question_type=serializer.validated_data['question_type']
                )
                
                if questions:
                    return Response({
                        'questions': questions,
                        'count': len(questions),
                        'message': 'Questions generated successfully'
                    }, status=status.HTTP_201_CREATED)
                else:
                    return Response(
                        {'error': 'Failed to generate questions'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
            
            except Exception as e:
                return Response(
                    {'error': f'Question generation error: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class HealthCheckView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        return Response({"status": "ok"})


class DocumentUploadAPIView(APIView):

    permission_classes = [IsAuthenticated]

    parser_classes = [MultiPartParser, FormParser]

    ALLOWED_EXTENSIONS = [".pdf", ".txt", ".md", ".docx"]

    def post(self, request):

        serializer = DocumentUploadSerializer(data=request.data, context={"request": request})

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        file = request.FILES.get("file")

        if not file:
            return Response({"error": "File is required"}, status=status.HTTP_400_BAD_REQUEST)

        document = serializer.save(source_type="upload")

        try:
            text = extract_text(document.file.path)
        except Exception as e:
            document.delete()
            return Response(
                {"error": f"Text extraction failed: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        document.content = text
        document.save()

        return Response(
            {
                "message": "Document uploaded successfully",
                "document_id": document.id
            },
            status=status.HTTP_201_CREATED
        )

class ScrapeDocumentAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        url = request.data.get("url")
        subject = request.data.get("subject")
        exam_type = request.data.get("exam_type")
        topic = request.data.get("topic", "")

        if not url:
            return Response({"error": "URL is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            document = scrape_and_store_document(url, subject, exam_type, topic)

            return Response(
                {
                    "message": "Document scraped successfully",
                    "document_id": document.id
                },
                status=status.HTTP_201_CREATED
            )

        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
    from .services.rag.document_cleaner import clean_document


class CleanDocumentAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        document_id = request.data.get("document_id")

        if not document_id:
            return Response({"error": "document_id required"}, status=400)

        try:
            document = Document.objects.get(id=document_id)

            clean_document(document)

            return Response({
                "message": "Document cleaned successfully"
            })

        except Document.DoesNotExist:
            return Response({"error": "Document not found"}, status=404)
        



class ChunkDocumentAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        document_id = request.data.get("document_id")

        if not document_id:
            return Response({"error": "document_id required"}, status=400)

        try:

            document = Document.objects.get(id=document_id)

            chunks = create_chunks(document)

            return Response({
                "message": "Document chunked successfully",
                "chunks_created": len(chunks)
            })

        except Document.DoesNotExist:
            return Response({"error": "Document not found"}, status=404)




class EmbedDocumentAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        document_id = request.data.get("document_id")

        if not document_id:
            return Response({"error": "document_id required"}, status=400)

        try:

            document = Document.objects.get(id=document_id)

            count = embed_document_chunks(document)

            return Response({
                "message": "Embeddings generated",
                "chunks_processed": count
            })

        except Document.DoesNotExist:
            return Response({"error": "Document not found"}, status=404)
        



class SemanticSearchAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request):

        query = request.data.get("query")

        if not query:
            return Response({"error": "query required"}, status=400)

        chunks = RAGService.retrieve_relevant_documents(query=query, user=request.user, top_k=5)

        response = []

        for chunk, score in chunks:
            response.append({
                "chunk_id": chunk.id,
                "content": chunk.content[:200],
                "score": float(score),
                "document_id": chunk.parent_document_id
            })

        return Response({"results": response})
    


class ProcessDocumentAPIView(APIView):

    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):

        serializer = DocumentUploadSerializer(data=request.data, context={"request": request})

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        file = request.FILES.get("file")

        if not file:
            return Response({"error": "File required"}, status=400)

        try:
            # 1. Save document
            document = serializer.save(source_type="upload")

            # 2. Run full pipeline
            result = process_document(document)

            return Response({
                "message": "Document fully processed",
                "document_id": document.id,
                **result
            }, status=201)

        except Exception as e:
            return Response({
                "error": str(e)
            }, status=500)