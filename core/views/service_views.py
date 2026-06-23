"""
Service catalog API views — CRUD (owner-only for CUD).
"""
from rest_framework import viewsets
from ..models import Service
from ..serializers import ServiceSerializer
from ..permissions import IsOwnerOrReadOnly


class ServiceViewSet(viewsets.ModelViewSet):
    """
    Service type catalog. All users can read; only owner can create/edit/delete.
    """
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [IsOwnerOrReadOnly]
    search_fields = ['name']
