"""
Service catalog API views — CRUD (owner-only for CUD).
"""
from rest_framework import viewsets, status
from rest_framework.response import Response
from ..models import Service
from ..serializers import ServiceSerializer
from ..permissions import IsOwnerOrReadOnly


class ServiceViewSet(viewsets.ModelViewSet):
    """
    Service type catalog. All users can read; only owner can create/edit/delete.
    """
    serializer_class = ServiceSerializer
    permission_classes = [IsOwnerOrReadOnly]
    search_fields = ['name']
    pagination_class = None

    def get_queryset(self):
        return Service.objects.filter(is_active=True, is_deleted=False)

    def create(self, request, *args, **kwargs):
        name = request.data.get('name', '').strip()
        existing = Service.objects.filter(name__iexact=name).first()
        if existing:
            if not existing.is_active:
                existing.is_active = True
                existing.save()
                serializer = self.get_serializer(existing)
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                return Response({'name': ['Service with this name already exists.']}, status=status.HTTP_400_BAD_REQUEST)
        return super().create(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        from django.utils import timezone
        instance = self.get_object()
        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
