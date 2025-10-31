import csv
from django.http import HttpResponse
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from payments.models import PaymentTransaction

User = get_user_model()


class AdminUsersView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        data = list(User.objects.all().values('id', 'username', 'email', 'role', 'is_verified', 'is_disabled'))
        return Response(data)


class AdminPaymentsView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        data = list(PaymentTransaction.objects.all().values('id', 'user_id', 'amount', 'currency', 'status', 'created_at'))
        return Response(data)


class ExportUsersCSVView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        response = HttpResponse(content_type='text/csv')
        response["Content-Disposition"] = 'attachment; filename="users.csv"'
        writer = csv.writer(response)
        writer.writerow(['id', 'username', 'email', 'role', 'is_verified', 'is_disabled'])
        for u in User.objects.all():
            writer.writerow([u.id, u.username, u.email, u.role, u.is_verified, u.is_disabled])
        return response


class ExportPaymentsCSVView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        response = HttpResponse(content_type='text/csv')
        response["Content-Disposition"] = 'attachment; filename="payments.csv"'
        writer = csv.writer(response)
        writer.writerow(['id', 'user_id', 'amount', 'currency', 'status', 'created_at'])
        for p in PaymentTransaction.objects.all():
            writer.writerow([p.id, p.user_id, p.amount, p.currency, p.status, p.created_at])
        return response
