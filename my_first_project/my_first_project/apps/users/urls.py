from django.urls import path
from . import views

urlpatterns = [
    path('usernames/<username:username>/count/', views.UsernameCountView.as_view()),
    path('mobiles/<mobile:phone_num>/count/', views.MobileCountView.as_view()),
    path('register/', views.RegisterView.as_view()),
    path('login/', views.LoginView.as_view()),
    path('logout/', views.LogoutView.as_view()),
    path('info/', views.UserInfoView.as_view()),
    path('emails/', views.EmailView.as_view()),
    path('emails/verification/', views.VerifyEmailView.as_view()),
    path('addresses/create/', views.CreateAddressView.as_view()),
    path('addresses/', views.AddressView.as_view()),
    path('addresses/<int:address_id>/', views.UpdateDestroyAddressView.as_view()),
    path('addresses/<int:address_id>/default/', views.DefaultAddressView.as_view()),
    path('addresses/<int:address_id>/title/', views.UpdateTitleAddressView.as_view()),
    path('password/', views.ChangePasswordView.as_view()),


]
