"""
Expense API views — CRUD for daily expenses.
"""
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as filters
from ..models import Expense
from ..serializers import ExpenseSerializer
from ..permissions import IsOwner


class ExpenseFilter(filters.FilterSet):
    class Meta:
        model = Expense
        fields = ['date']


class ExpenseViewSet(viewsets.ModelViewSet):
    """Expense CRUD — owner only."""
    serializer_class = ExpenseSerializer
    permission_classes = [IsOwner]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ExpenseFilter

    def get_queryset(self):
        return Expense.objects.filter(is_deleted=False)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    def destroy(self, request, *args, **kwargs):
        from django.utils import timezone
        from rest_framework import status
        from rest_framework.response import Response
        instance = self.get_object()
        instance.is_deleted = True
        instance.deleted_at = timezone.now()
        instance.save(update_fields=['is_deleted', 'deleted_at'])
        return Response(status=status.HTTP_204_NO_CONTENT)
