"""
Recycle Bin API views — manage soft-deleted items.
"""
from datetime import timedelta
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from ..models import (
    ServiceEntry, Expense, Customer, Service, User,
    JobUpdate, EducationApplication, PublicService, WhyChooseUsPoint
)
from ..serializers import (
    ServiceEntryListSerializer, ExpenseSerializer, CustomerSerializer,
    ServiceSerializer, UserSerializer, JobUpdateSerializer,
    EducationApplicationSerializer, PublicServiceSerializer, WhyChooseUsPointSerializer
)
from ..permissions import IsOwner


class RecycleBinView(APIView):
    """
    Owner-only view for Recycle Bin.
    Handles listing, restoring, and permanently deleting items.
    Also auto-cleans items older than 10 days.
    """
    permission_classes = [IsOwner]

    def _cleanup_old_items(self):
        """Permanently delete items older than 10 days."""
        cutoff_date = timezone.now() - timedelta(days=10)
        ServiceEntry.objects.filter(is_deleted=True, deleted_at__lt=cutoff_date).delete()
        Expense.objects.filter(is_deleted=True, deleted_at__lt=cutoff_date).delete()
        Customer.objects.filter(is_deleted=True, deleted_at__lt=cutoff_date).delete()
        Service.objects.filter(is_deleted=True, deleted_at__lt=cutoff_date).delete()
        User.objects.filter(is_deleted=True, deleted_at__lt=cutoff_date).delete()
        JobUpdate.objects.filter(is_deleted=True, deleted_at__lt=cutoff_date).delete()
        EducationApplication.objects.filter(is_deleted=True, deleted_at__lt=cutoff_date).delete()
        PublicService.objects.filter(is_deleted=True, deleted_at__lt=cutoff_date).delete()
        WhyChooseUsPoint.objects.filter(is_deleted=True, deleted_at__lt=cutoff_date).delete()

    def get(self, request):
        self._cleanup_old_items()

        entries = ServiceEntry.objects.filter(is_deleted=True).order_by('-deleted_at')
        expenses = Expense.objects.filter(is_deleted=True).order_by('-deleted_at')
        customers = Customer.objects.filter(is_deleted=True).order_by('-deleted_at')
        services = Service.objects.filter(is_deleted=True).order_by('-deleted_at')
        staff = User.objects.filter(is_deleted=True).order_by('-deleted_at')
        jobs = JobUpdate.objects.filter(is_deleted=True).order_by('-deleted_at')
        education_apps = EducationApplication.objects.filter(is_deleted=True).order_by('-deleted_at')
        public_services = PublicService.objects.filter(is_deleted=True).order_by('-deleted_at')
        why_choose_us = WhyChooseUsPoint.objects.filter(is_deleted=True).order_by('-deleted_at')

        return Response({
            'entries': ServiceEntryListSerializer(entries, many=True).data,
            'expenses': ExpenseSerializer(expenses, many=True).data,
            'customers': CustomerSerializer(customers, many=True).data,
            'services': ServiceSerializer(services, many=True).data,
            'staff': UserSerializer(staff, many=True).data,
            'jobs': JobUpdateSerializer(jobs, many=True).data,
            'education_apps': EducationApplicationSerializer(education_apps, many=True).data,
            'public_services': PublicServiceSerializer(public_services, many=True).data,
            'why_choose_us': WhyChooseUsPointSerializer(why_choose_us, many=True).data,
        })

    def post(self, request):
        """
        Handle restore or hard delete.
        Expected body:
        {
            "action": "restore" | "hard_delete",
            "type": "entry" | "expense",
            "id": 123
        }
        """
        action = request.data.get('action')
        item_type = request.data.get('type')
        item_id = request.data.get('id')

        if not all([action, item_type, item_id]):
            return Response({'detail': 'Missing parameters'}, status=status.HTTP_400_BAD_REQUEST)

        MODEL_MAP = {
            'entry': ServiceEntry,
            'expense': Expense,
            'customer': Customer,
            'service': Service,
            'staff': User,
            'job': JobUpdate,
            'education': EducationApplication,
            'public_service': PublicService,
            'why_choose_us': WhyChooseUsPoint,
        }
        model_class = MODEL_MAP.get(item_type)
        
        if not model_class:
            return Response({'detail': 'Invalid type'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            item = model_class.objects.get(id=item_id, is_deleted=True)
        except model_class.DoesNotExist:
            return Response({'detail': 'Item not found'}, status=status.HTTP_404_NOT_FOUND)

        if action == 'restore':
            if item_type == 'staff':
                item.is_active = True
                item.role = 'staff'
                item.username = item.username.split('_del_')[0]
                item.is_deleted = False
                item.deleted_at = None
                item.save(update_fields=['is_active', 'role', 'username', 'is_deleted', 'deleted_at'])
            elif hasattr(item, 'is_active'):
                item.is_active = True
                item.is_deleted = False
                item.deleted_at = None
                item.save(update_fields=['is_active', 'is_deleted', 'deleted_at'])
            else:
                item.is_deleted = False
                item.deleted_at = None
                item.save(update_fields=['is_deleted', 'deleted_at'])
            return Response({'detail': 'Item restored successfully'})
        
        elif action == 'hard_delete':
            item.delete()
            return Response({'detail': 'Item permanently deleted'})
            
        return Response({'detail': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)
