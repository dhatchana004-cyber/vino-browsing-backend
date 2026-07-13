"""
Customer API views — List/Search, Create, Detail with history.
"""
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as filters
from ..models import Customer
from ..serializers import CustomerSerializer, CustomerDetailSerializer


class CustomerFilter(filters.FilterSet):
    date_from = filters.DateFilter(field_name='entries__date', lookup_expr='gte', distinct=True)
    date_to = filters.DateFilter(field_name='entries__date', lookup_expr='lte', distinct=True)

    class Meta:
        model = Customer
        fields = ['phone']


class CustomerViewSet(viewsets.ModelViewSet):
    """
    Customer CRUD with search by name/phone.
    Detail view includes full service entry history.
    """
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = CustomerFilter
    search_fields = ['name', 'phone']
    ordering_fields = ['name', 'created_at']

    def get_queryset(self):
        return Customer.objects.filter(is_deleted=False).prefetch_related('entries')

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CustomerDetailSerializer
        return CustomerSerializer

    def destroy(self, request, *args, **kwargs):
        from django.utils import timezone
        instance = self.get_object()
        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.save()
        from rest_framework import status
        from rest_framework.response import Response
        return Response(status=status.HTTP_204_NO_CONTENT)
