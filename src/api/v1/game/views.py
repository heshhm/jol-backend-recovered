from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination

from src.services.game.models import GameHistory
from .serializers import GameHistoryCreateSerializer, GameHistorySerializer

from django.utils import timezone
from django.db.models import Sum, When, Case, IntegerField, F
from datetime import timedelta

from src.services.user.models import UserProfile
from django.db.models import Count

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
            out_ser = GameHistorySerializer(game)
            return Response(out_ser.data, status=status.HTTP_201_CREATED)
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

class LeaderboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        period = request.query_params.get("period", "all_time")
        valid_periods = ["today", "this_week", "this_month", "all_time"]
        if period not in valid_periods:
            return Response(
                {"error": f"Invalid period. Use: {valid_periods}"},
                status=status.HTTP_400_BAD_REQUEST
            )

        page_size = min(int(request.query_params.get("page_size", 50)), 100)
        page = max(int(request.query_params.get("page", 1)), 1)
        offset = (page - 1) * page_size

        now = timezone.now()
        start_date = {
            "today": now.replace(hour=0, minute=0, second=0, microsecond=0),
            "this_week": now - timedelta(days=now.weekday()),
            "this_month": now.replace(day=1, hour=0, minute=0, second=0, microsecond=0),
            "all_time": None,
        }.get(period)

        qs = GameHistory.objects.all()

        if start_date:
            qs = qs.filter(timestamp__gte=start_date)

        leaderboard_data = (
            qs
            .values("player")
            .annotate(
                period_points=Sum("points_earned"),  # ← NOW A REAL FIELD
                games_played=Count("id")
            )
            .order_by("-period_points")
        )

        total = leaderboard_data.count()
        paginated = leaderboard_data[offset:offset + page_size]

        user_ids = [item["player"] for item in paginated]
        profiles = UserProfile.objects.filter(user_id__in=user_ids).select_related("user")
        profile_map = {p.user_id: p for p in profiles}

        results = []
        for idx, item in enumerate(paginated):
            profile = profile_map.get(item["player"])
            if not profile:
                continue
            results.append({
                "rank": offset + idx + 1,
                "user_id": item["player"],
                "username": profile.user.username,
                "email": profile.user.email,
                "avatar": profile.avatar.url if profile.avatar else None,
                "total_points": item["period_points"] or 0,
                "games_played": item["games_played"],
            })

        return Response({
            "period": period,
            "count": total,
            "page": page,
            "page_size": page_size,
            "results": results
        })
