from django.urls import path, include
from django.http import JsonResponse

def root(request):
    return JsonResponse({'message': 'Бізнес логіка працює! Django API'})

urlpatterns = [
    path('', root),
    path('', include('school.urls')),
]
