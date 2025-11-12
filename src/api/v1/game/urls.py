# game/urls.py
from django.urls import path
from .views import AddGameHistoryView, GameHistoryListView

app_name = "game"

urlpatterns = [
    path("add-game/", AddGameHistoryView.as_view(), name="add-game"),
    path("list/", GameHistoryListView.as_view(), name="game-list"),
]