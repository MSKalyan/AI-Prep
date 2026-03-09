from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .services.dashboard_service import DashboardService


class DashboardView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        data = DashboardService.get_dashboard_summary(
            request.user
        )

        return Response(data)