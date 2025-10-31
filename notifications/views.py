from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Notification, DeviceToken
from .serializers import NotificationSerializer, DeviceTokenSerializer


class NotificationListView(APIView):
    def get(self, request):
        qs = Notification.objects.filter(user=request.user).order_by('-created_at')
        return Response(NotificationSerializer(qs, many=True).data)


class MarkAsReadView(APIView):
    def patch(self, request, pk: int):
        try:
            notif = Notification.objects.get(pk=pk, user=request.user)
        except Notification.DoesNotExist:
            return Response({"detail": "Not found"}, status=status.HTTP_404_NOT_FOUND)
        notif.read_status = True
        notif.save(update_fields=["read_status"])
        return Response({"message": "Marked as read"})


class RegisterTokenView(APIView):
    def post(self, request):
        ser = DeviceTokenSerializer(data=request.data)
        ser.is_valid(raise_exception=True)
        DeviceToken.objects.update_or_create(user=request.user, token=ser.validated_data['token'])
        return Response({"message": "Token registered"})
