from django.urls import path
from . import views

urlpatterns = [
    # Stripe endpoints
    path('create-session/', views.CreateCheckoutSessionView.as_view(), name='create-checkout-session'),
    path('webhook/', views.StripeWebhookView.as_view(), name='stripe-webhook'),

    # PayPal endpoints
    path('paypal/create-order/', views.CreatePayPalOrderView.as_view(), name='paypal-create-order'),
    path('paypal/create-subscription/', views.CreatePayPalSubscriptionView.as_view(), name='paypal-create-subscription'),
    path('paypal/execute-payment/', views.ExecutePayPalPaymentView.as_view(), name='paypal-execute-payment'),
    path('paypal/webhook/', views.PayPalWebhookView.as_view(), name='paypal-webhook'),
    path('paypal/cancel/', views.CancelPayPalSubscriptionView.as_view(), name='paypal-cancel-subscription'),

    # Common endpoints


    path('subscription/', views.UserSubscriptionView.as_view(), name='user-subscription'),
    path('cancel/', views.CancelSubscriptionView.as_view(), name='cancel-subscription'),
    path('history/', views.PaymentHistoryView.as_view(), name='payment-history'),
    path('check-status/', views.CheckPaymentStatusView.as_view(), name='check-payment-status'),

    # Success and cancel pages for mobile app redirects
    path('success/', views.PaymentSuccessView.as_view(), name='payment-success'),
    path('cancelled/', views.PaymentCancelView.as_view(), name='payment-cancelled'),
]
