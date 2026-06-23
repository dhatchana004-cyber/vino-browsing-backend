import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vino.settings')
django.setup()

from core.models import ServiceEntry
from core.views.entry_views import ServiceEntryFilter

queryset = ServiceEntry.objects.all()

f1 = ServiceEntryFilter({'date_from': '2026-06-01', 'date_to': '2026-06-10'}, queryset=queryset)
print("Filter 2026-06-01 to 2026-06-10 count:", f1.qs.count())

f2 = ServiceEntryFilter({'date_from': '2026-06-16', 'date_to': '2026-06-17'}, queryset=queryset)
print("Filter 2026-06-16 to 2026-06-17 count:", f2.qs.count())

f3 = ServiceEntryFilter({}, queryset=queryset)
print("No filter count:", f3.qs.count())
