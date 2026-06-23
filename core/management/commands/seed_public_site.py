from django.core.management.base import BaseCommand
from core.models import SiteSettings, WhyChooseUsPoint, PublicService, JobUpdate
from datetime import date, timedelta

class Command(BaseCommand):
    help = 'Seeds the database with default public site data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding public site data...')

        # 1. Site Settings
        settings = SiteSettings.get_settings()
        settings.shop_name = "VINO Browsing Center"
        settings.address = "No. 12, Main Road\nNear Bus Stand\nCity, Tamil Nadu - 600000"
        settings.hours = "9:00 AM - 9:00 PM"
        settings.holiday = "Sunday Holiday"
        settings.phone = "+91 98765 43210"
        settings.whatsapp = "+91 98765 43210"
        settings.email = "contact@vinobrowsing.com"
        settings.map_url = "https://maps.google.com/?q=VINO+Browsing"
        settings.hero_title = "Your One-Stop Digital Service Center"
        settings.hero_service_tags = "Browsing, Printouts, Tickets, Passport"
        settings.save()

        # 2. Why Choose Us
        WhyChooseUsPoint.objects.all().delete()
        points = [
            "Fast and reliable high-speed internet",
            "Expert assistance for all online applications",
            "Secure and private browsing environment",
            "Affordable pricing for printing and scanning"
        ]
        for i, text in enumerate(points):
            WhyChooseUsPoint.objects.create(text=text, order=i+1)

        # 3. Services (12 cards)
        PublicService.objects.all().delete()
        services = [
            {"title": "Browsing & Internet", "icon": "🌐", "desc": "High-speed browsing for your work and entertainment needs."},
            {"title": "Print & Scan", "icon": "🖨️", "desc": "Color and B/W printing, scanning, and lamination services."},
            {"title": "Train & Bus Tickets", "icon": "🎫", "desc": "IRCTC train tickets and private bus bookings."},
            {"title": "Passport Services", "icon": "🛂", "desc": "New passport application and renewal assistance."},
            {"title": "PAN Card", "icon": "💳", "desc": "Apply for new PAN card or update existing details."},
            {"title": "Aadhar Services", "icon": "🆔", "desc": "Aadhar download, printouts, and appointment booking."},
            {"title": "Voter ID", "icon": "🗳️", "desc": "New Voter ID registration and corrections."},
            {"title": "Money Transfer", "icon": "💸", "desc": "Instant domestic money transfer services."},
            {"title": "Exam Applications", "icon": "📝", "desc": "Assistance with TNPSC, UPSC, and college admissions."},
            {"title": "DTP & Typing", "icon": "⌨️", "desc": "Professional typing in English and Tamil."},
            {"title": "Mobile Recharge", "icon": "📱", "desc": "Prepaid and postpaid mobile recharges."},
            {"title": "PF Claim Services", "icon": "💼", "desc": "EPF withdrawal and UAN activation."}
        ]
        for i, svc in enumerate(services):
            PublicService.objects.create(title=svc['title'], icon=svc['icon'], description=svc['desc'], order=i+1, is_active=True)

        # 4. Job Updates (10 jobs)
        JobUpdate.objects.all().delete()
        today = date.today()
        jobs = [
            {"title": "TNPSC Group 4 Notification", "desc": "Apply before last date. Bring passport size photo and aadhar."},
            {"title": "SSC CHSL 2026", "desc": "Combined Higher Secondary Level exam notification out."},
            {"title": "Railway RRB NTPC", "desc": "Mega recruitment drive for non-technical popular categories."},
            {"title": "IBPS PO & Clerk", "desc": "Bank exam applications are now open. Apply here!"},
            {"title": "TCS Off-Campus Drive", "desc": "Freshers registration started for 2026 batch."},
            {"title": "Post Office GDS", "desc": "Gramin Dak Sevak vacancies announced. Apply with 10th marks."},
            {"title": "Police Constable (TNUSRB)", "desc": "Physical test dates and written exam applications."},
            {"title": "Madras High Court Jobs", "desc": "Office assistant and clerk vacancies open."},
            {"title": "NEET 2026 Application", "desc": "Medical entrance exam applications started. Bring photo and sign."},
            {"title": "Engineering Counselling (TNEA)", "desc": "Online registration for B.E/B.Tech admissions."}
        ]
        for i, job in enumerate(jobs):
            JobUpdate.objects.create(
                title=job['title'], 
                description=job['desc'], 
                start_date=today - timedelta(days=i), 
                end_date=today + timedelta(days=30), 
                is_active=True
            )

        self.stdout.write(self.style.SUCCESS('[+] Successfully seeded public site data!'))
