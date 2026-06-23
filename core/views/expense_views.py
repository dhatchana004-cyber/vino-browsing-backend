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
        return Expense.objects.all()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
