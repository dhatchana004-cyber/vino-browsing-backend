"""
Service Entry API views — CRUD with role-based filtering.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters import rest_framework as filters
from ..models import ServiceEntry
from ..serializers import (
    ServiceEntrySerializer,
    ServiceEntryListSerializer,
    StatusUpdateSerializer,
)


class ServiceEntryFilter(filters.FilterSet):
    """Custom filter for service entries with date range and SRN support."""
    date_from = filters.DateFilter(field_name='date', lookup_expr='gte')
    date_to = filters.DateFilter(field_name='date', lookup_expr='lte')
    has_srn = filters.BooleanFilter(method='filter_has_srn')

    class Meta:
        model = ServiceEntry
        fields = ['staff', 'service', 'status', 'date']

    def filter_has_srn(self, queryset, name, value):
        if value:
            return queryset.exclude(srn_number='')
        return queryset


class ServiceEntryViewSet(viewsets.ModelViewSet):
    """
    Service Entry CRUD.
    - Owner sees all entries.
    - Staff sees only own entries.
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = ServiceEntryFilter
    search_fields = ['customer_name', 'phone', 'srn_number']
    ordering_fields = ['created_at', 'date', 'amount']

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return ServiceEntryListSerializer
        return ServiceEntrySerializer

    def get_queryset(self):
        qs = ServiceEntry.objects.select_related('service', 'staff', 'customer').filter(is_deleted=False)
        if self.request.user.role == 'staff':
            qs = qs.filter(staff=self.request.user)
        return qs

    def perform_create(self, serializer):
        # If staff, force assignment to self
        if self.request.user.role == 'staff':
            service = serializer.validated_data.get('service')
            if service:
                service_name = service.name.lower()
                is_restricted = 'pan new' in service_name or 'pan correction' in service_name or 'pan ' in service_name
                if is_restricted and not self.request.user.staff_permissions.filter(permission='edit_records').exists():
                    from rest_framework.exceptions import PermissionDenied
                    raise PermissionDenied('You do not have permission to create PAN records.')
            serializer.save(staff=self.request.user)
        else:
            serializer.save()

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.role == 'staff':
            service_name = instance.service.name.lower()
            is_restricted = 'pan new' in service_name or 'pan correction' in service_name or 'pan ' in service_name
            if is_restricted and not request.user.staff_permissions.filter(permission='edit_records').exists():
                from rest_framework import status
                from rest_framework.response import Response
                return Response({'detail': 'You do not have permission to edit PAN records.'}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.role == 'staff':
            service_name = instance.service.name.lower()
            is_restricted = 'pan new' in service_name or 'pan correction' in service_name or 'pan ' in service_name
            if is_restricted and not request.user.staff_permissions.filter(permission='edit_records').exists():
                from rest_framework import status
                from rest_framework.response import Response
                return Response({'detail': 'You do not have permission to edit PAN records.'}, status=status.HTTP_403_FORBIDDEN)
        return super().partial_update(request, *args, **kwargs)

    @action(detail=True, methods=['patch'], url_path='status')
    def update_status(self, request, pk=None):
        """PATCH /api/entries/{id}/status/ — Update status only."""
        entry = self.get_object()
        

        serializer = StatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        entry.status = serializer.validated_data['status']
        entry.save(update_fields=['status'])
        return Response(ServiceEntryListSerializer(entry).data)

    def destroy(self, request, *args, **kwargs):
        from django.utils import timezone
        instance = self.get_object()
        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.save(update_fields=['is_deleted', 'deleted_at'])
        return Response(status=status.HTTP_204_NO_CONTENT)
