from django.urls import path

from api import views

account_url_patterns = [
    path('api/hijack/', views.HijackView.as_view(), name='hijack'),


    path('api/api-token-auth/', views.TokenView.as_view(), name='token'),
    path('api/pos/api-token-auth/', views.TokenView.as_view(is_pos=True), name='token_pos'),

    path('api/logout/', views.LogoutView.as_view(), name='logout'),
    path('api/pos/logout/', views.LogoutView.as_view(is_pos=True), name='logout_pos'),
    path('api/logout/everywhere/', views.LogoutView.as_view(logout_everywhere=True), name='logout_everywhere'),

    path('api/signup/', views.SignupView.as_view(), name='signup'),
    path('api/contact/', views.ContactView.as_view(), name='contact'),
    path('api/ws/ticket/', views.WebSocketTicketView.as_view()),

    path('api/password/change/', views.PasswordChangeView.as_view(),name='password_change'),
    path('api/password/reset/', views.ResetPasswordRequestToken.as_view(),name='password_reset'),
    path('api/reset_password/validate_token/', views.ResetPasswordValidateToken.as_view(),name='password_validate_token'),
    path('api/password/reset/confirm/', views.ResetPasswordConfirm.as_view(),name='password_reset_confirm'),


    path('api/email-receipt/', views.ReceiptEmailView.as_view(), name='email_receipt'),
]


