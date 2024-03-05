from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProfileViewSet

router = DefaultRouter()
router.register(r'profiles', ProfileViewSet, basename='profile')

urlpatterns = [
    #path('profiles/', ProfileListView.as_view(), name='profile-list'),
    path('', include(router.urls)),
    # Other URL patterns...
]