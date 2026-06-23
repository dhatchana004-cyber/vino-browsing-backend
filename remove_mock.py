import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vino.settings')
django.setup()

from core.models import ServiceEntry, Expense, OpeningBalance, Attendance, Customer

print("Deleting all mock records...")
ServiceEntry.objects.all().delete()
Expense.objects.all().delete()
Attendance.objects.all().delete()
OpeningBalance.objects.all().delete()
Customer.objects.all().delete()

print("Mock data removed successfully.")
