from django.urls import path
from .views import home, profile, register

urlpatterns = [
    path('', home, name='home'),
    path('profile/', profile, name='profile'),
    path('register/', register, name='register'),
]