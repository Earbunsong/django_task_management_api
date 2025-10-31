from django.urls import path
from . import views

urlpatterns = [
    path('create-session/', views.CreateCheckoutSessionView.as_view(), name='create-checkout-session'),
    path('webhook/', views.StripeWebhookView.as_view(), name='stripe-webhook'),
    path('subscription/', views.UserSubscriptionView.as_view(), name='user-subscription'),
    path('cancel/', views.CancelSubscriptionView.as_view(), name='cancel-subscription'),
    path('history/', views.PaymentHistoryView.as_view(), name='payment-history'),
]
