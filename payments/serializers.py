from rest_framework import serializers
from .models import Subscription, PaymentTransaction


class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ('plan_type', 'start_date', 'end_date', 'payment_status')


class PaymentTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentTransaction
        fields = ('id', 'stripe_session_id', 'amount', 'currency', 'status', 'created_at')
        read_only_fields = ('id', 'created_at')
