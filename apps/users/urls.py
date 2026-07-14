from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import AddressDetailView, AddressListCreateView, LoginView, ProfileView, RegisterView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("addresses/", AddressListCreateView.as_view(), name="addresses"),
    path("addresses/<int:pk>/", AddressDetailView.as_view(), name="address-detail"),
]
