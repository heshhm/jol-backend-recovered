from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination

from src.services.game.models import GameHistory
from .serializers import GameHistoryCreateSerializer, GameHistorySerializer


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100


class AddGameHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Pass request to serializer context
        serializer = GameHistoryCreateSerializer(
            data=request.data,
            context={"request": request}
        )
        if serializer.is_valid():
            game = serializer.save()
            return Response(
                {"detail": "Game saved.", "match_id": str(game.match_id)},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class GameHistoryListView(APIView):
    """GET /api/v1/games/ - Paginated personal game history"""
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get(self, request):
        queryset = GameHistory.objects.filter(player=request.user).order_by("-timestamp")
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)

        if page is not None:
            serializer = GameHistorySerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = GameHistorySerializer(queryset, many=True)
        return Response(serializer.data)