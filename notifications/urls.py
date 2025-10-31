from django.urls import path
from . import views

urlpatterns = [
    path('', views.NotificationListView.as_view(), name='notification-list'),
    path('<int:pk>/read/', views.MarkAsReadView.as_view(), name='notification-read'),
    path('register-token/', views.RegisterTokenView.as_view(), name='register-token'),
]
