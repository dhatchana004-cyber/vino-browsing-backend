"""
Seed data command — Creates owner, staff, and service types.

Usage: python manage.py seed_data
"""
from django.core.management.base import BaseCommand
from core.models import User, Service


class Command(BaseCommand):
    help = 'Seeds the database with initial services and staff users'

    def handle(self, *args, **options):
        self.stdout.write('[*] Seeding VINO database...\n')

        # ---- Create Owner ----
        owner, created = User.objects.get_or_create(
            username='vino',
            defaults={
                'first_name': 'Vino',
                'last_name': 'Owner',
                'role': 'owner',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if created:
            owner.set_password('vino@123')
            owner.save()
            self.stdout.write(self.style.SUCCESS('[+] Owner created: vino / vino@123'))
        else:
            self.stdout.write('   Owner "vino" already exists')

        # ---- Create Staff Users ----
        staff_users = [
            ('divya', 'Divya'),
            ('raji', 'Raji'),
            ('hari', 'Hari'),
            ('vennila', 'Vennila'),
            ('vijay', 'Vijay'),
            ('durai', 'Durai'),
            ('ranith', 'Ranith'),
        ]
        for username, first_name in staff_users:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'first_name': first_name,
                    'role': 'staff',
                }
            )
            if created:
                user.set_password('staff@123')
                user.save()
                self.stdout.write(self.style.SUCCESS(f'[+] Staff created: {username} / staff@123'))
            else:
                self.stdout.write(f'   Staff "{username}" already exists')

        # ---- Create Services ----
        services = [
            'Aadhaar Update',
            'Aadhaar Enrollment',
            'Passport',
            'Driving License',
            'Ration Card',
            'Voter ID',
            'Income Certificate',
            'Community Certificate',
            'TNEB',
            'Police Complaint',
            'CM Cell Petition',
            'TNPDS',
            'TNUWWB',
            'MRB Application',
            'PVR',
            'PAN Card',
            'Esevai Certificate',
            'Other Service',
        ]
        created_count = 0
        for service_name in services:
            _, created = Service.objects.get_or_create(name=service_name)
            if created:
                created_count += 1

        self.stdout.write(self.style.SUCCESS(f'[+] {created_count} services created'))
        self.stdout.write(self.style.SUCCESS('\n[OK] Seed complete! Login at /api/auth/login/'))
