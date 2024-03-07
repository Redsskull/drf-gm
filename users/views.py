from rest_framework import viewsets
from .models import Profile
from .serializers import ProfileSerializer
from rest_framework.response import Response


class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer

    
