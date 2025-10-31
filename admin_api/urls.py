from django.urls import path
from .views import AdminUsersView, AdminPaymentsView, ExportUsersCSVView, ExportPaymentsCSVView

urlpatterns = [
    path('users/', AdminUsersView.as_view(), name='admin-users'),
    path('payments/', AdminPaymentsView.as_view(), name='admin-payments'),
    path('export/users/', ExportUsersCSVView.as_view(), name='admin-export-users'),
    path('export/payments/', ExportPaymentsCSVView.as_view(), name='admin-export-payments'),
]
