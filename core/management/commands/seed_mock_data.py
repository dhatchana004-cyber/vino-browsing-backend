import random
from datetime import timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import User, Service, Customer, ServiceEntry, Expense, OpeningBalance, Attendance

class Command(BaseCommand):
    help = 'Seeds the database with 1 month of mock data for testing'

    def handle(self, *args, **options):
        self.stdout.write('[*] Generating 1 month of mock data...')

        owner = User.objects.filter(role='owner').first()
        if not owner:
            self.stdout.write(self.style.ERROR('Owner not found. Please run "python manage.py seed_data" first.'))
            return

        staff_users = list(User.objects.filter(role='staff'))
        services = list(Service.objects.all())

        if not staff_users or not services:
            self.stdout.write(self.style.ERROR('Staff or Services not found. Please run "python manage.py seed_data" first.'))
            return

        self.stdout.write('[*] Clearing old Service Entries and Expenses...')
        ServiceEntry.objects.all().delete()
        Expense.objects.all().delete()
        Attendance.objects.all().delete()
        OpeningBalance.objects.all().delete()

        end_date = timezone.localdate()
        start_date = end_date - timedelta(days=30)

        # Generate Customers
        names = ["Aarav", "Vihaan", "Vivaan", "Ananya", "Diya", "Advik", "Kavya", "Dhruv", "Kabir", "Saanvi", "Reyansh", "Krishna", "Ishaan", "Shaurya", "Atharv", "Mira", "Priya", "Rahul", "Karan", "Nisha"]
        last_names = ["Patel", "Sharma", "Kumar", "Singh", "Das", "Nair", "Rao", "Iyer", "Pillai", "Gowda", "Reddy", "Menon", "Jain", "Gupta", "Desai"]
        
        customers = []
        for i in range(50):
            name = f"{random.choice(names)} {random.choice(last_names)}"
            phone = f"98{random.randint(10000000, 99999999)}"
            c, _ = Customer.objects.get_or_create(phone=phone, defaults={'name': name})
            customers.append(c)

        # Generate Data Day by Day
        current_date = start_date
        entries_created = 0
        expenses_created = 0

        # Expense titles
        expense_titles = ["Stationery", "Electricity Bill", "Internet Bill", "Tea/Coffee Snacks", "Printer Ink", "Paper Reams", "Water Can", "Cleaning Supplies"]

        while current_date <= end_date:
            # 1. Opening Balance
            OpeningBalance.objects.update_or_create(
                date=current_date,
                defaults={'amount': Decimal(random.randint(500, 2000)), 'set_by': owner}
            )

            # 2. Staff Attendance (randomly 5-6 staff present)
            present_staff = random.sample(staff_users, k=random.randint(4, len(staff_users)))
            for staff in present_staff:
                # Random time between 8 AM and 9 AM
                hour = random.randint(8, 9)
                minute = random.randint(10, 59)
                login_time_naive = timezone.datetime.combine(current_date, timezone.datetime.strptime(f"{hour:02d}:{minute:02d}:00", "%H:%M:%S").time())
                login_time = timezone.make_aware(login_time_naive)
                
                # Random time between 6 PM and 8 PM
                hour = random.randint(18, 20)
                minute = random.randint(10, 59)
                logout_time_naive = timezone.datetime.combine(current_date, timezone.datetime.strptime(f"{hour:02d}:{minute:02d}:00", "%H:%M:%S").time())
                logout_time = timezone.make_aware(logout_time_naive)
                
                Attendance.objects.filter(staff=staff, date=current_date).delete()
                Attendance.objects.create(
                    staff=staff,
                    date=current_date,
                    login_time=login_time,
                    logout_time=logout_time,
                    working_hours=logout_time - login_time
                )

            # 3. Expenses (0-2 per day)
            for _ in range(random.randint(0, 2)):
                Expense.objects.create(
                    title=random.choice(expense_titles),
                    amount=Decimal(random.randint(50, 500)),
                    date=current_date,
                    created_by=owner
                )
                expenses_created += 1

            # 4. Service Entries (20-60 per day)
            num_entries = random.randint(20, 60)
            for _ in range(num_entries):
                service = random.choice(services)
                staff = random.choice(present_staff)
                customer = random.choice(customers)
                
                amount = Decimal(random.choice([50, 100, 150, 200, 300, 500]))
                charge = Decimal(random.randint(10, int(float(amount) * 0.4))) if amount > 50 else Decimal('10')
                profit = amount - charge

                status = random.choices(['pending', 'processing', 'completed', 'rejected'], weights=[10, 20, 65, 5])[0]

                # 30% chance to have SRN
                srn = f"SRN{random.randint(10000, 99999)}" if random.random() < 0.3 else ""
                
                hour = random.randint(10, 17)
                minute = random.randint(10, 59)
                created_at_naive = timezone.datetime.combine(current_date, timezone.datetime.strptime(f"{hour:02d}:{minute:02d}:00", "%H:%M:%S").time())
                created_at = timezone.make_aware(created_at_naive)

                entry = ServiceEntry.objects.create(
                    service=service,
                    staff=staff,
                    customer=customer,
                    customer_name=customer.name,
                    phone=customer.phone,
                    amount=amount,
                    charge=charge,
                    profit=profit,
                    status=status,
                    srn_number=srn,
                    date=current_date,
                )
                # Force override created_at
                ServiceEntry.objects.filter(id=entry.id).update(created_at=created_at)
                entries_created += 1

            current_date += timedelta(days=1)

        self.stdout.write(self.style.SUCCESS(f'[+] Successfully created {entries_created} Service Entries and {expenses_created} Expenses over 30 days!'))
