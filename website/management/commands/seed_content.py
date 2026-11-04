"""Fill empty content tables with SAMPLE content.   Usage:  python manage.py seed_content"""
from django.core.management.base import BaseCommand

from website.models import (
    Milestone, Product, Project, Service, SiteSettings, Stat, TeamMember, Testimonial, Value,
)

DATA = {
    Stat: [
        {"value": "10+", "label": "Years of experience"},
        {"value": "150+", "label": "Projects delivered"},
        {"value": "40+", "label": "Skilled engineers"},
        {"value": "24/7", "label": "Support desk"},
    ],
    Service: [
        {"icon": "💻", "title": "Software & App Development", "summary": "Custom websites, mobile apps, portals and business management systems."},
        {"icon": "🌐", "title": "Networking & Connectivity", "summary": "LAN and Wi-Fi design, structured cabling, VPN and internet installation."},
        {"icon": "🛡️", "title": "Cybersecurity", "summary": "Security audits, firewalls, antivirus deployment and staff awareness training."},
        {"icon": "🔧", "title": "IT Support & Maintenance", "summary": "Helpdesk, hardware repair, annual maintenance contracts and backups."},
        {"icon": "📹", "title": "CCTV & Access Control", "summary": "Surveillance, biometric attendance and smart door systems."},
        {"icon": "🎓", "title": "Training & Consulting", "summary": "Digital skills courses, ICT consulting and project advisory."},
    ],
    Product: [
        {"category": "software", "name": "XYZ School Manager", "summary": "Admissions, results, fees and parent communication in one system."},
        {"category": "software", "name": "XYZ Retail POS", "summary": "Point of sale, inventory and sales reports for shops and supermarkets."},
        {"category": "software", "name": "XYZ Payroll & HR", "summary": "Staff records, attendance, payroll and leave tracking."},
        {"category": "hardware", "name": "Laptops & desktops", "summary": "Business and student computers", "includes": "Setup and warranty"},
        {"category": "hardware", "name": "Networking kits", "summary": "Routers, switches, access points", "includes": "Installation"},
        {"category": "hardware", "name": "CCTV packages", "summary": "Cameras, DVR/NVR and storage", "includes": "Mounting and training"},
        {"category": "hardware", "name": "Solar & power backup", "summary": "Inverters and UPS for IT equipment", "includes": "Sizing advice"},
    ],
    Project: [
        {"sector": "Education", "title": "School results portal", "summary": "Online result checking and fee payment for a secondary school."},
        {"sector": "Business", "title": "Multi-branch retail network", "summary": "Connected POS and stock control across three outlets."},
        {"sector": "Public sector", "title": "Office LAN and CCTV", "summary": "Structured cabling and surveillance for a government office."},
        {"sector": "Healthcare", "title": "Clinic records system", "summary": "Digital patient records and appointment booking."},
    ],
    Testimonial: [
        {"quote": "Professional, punctual and easy to work with.", "author": "Sample client", "role": "School Proprietor"},
        {"quote": "Our network has not gone down since installation.", "author": "Sample client", "role": "Office Manager"},
    ],
    TeamMember: [
        {"name": "Managing Director", "role": "Leadership", "bio": "Sets strategy and oversees client relationships."},
        {"name": "Head of Engineering", "role": "Engineering", "bio": "Leads software, network and security teams."},
        {"name": "Head of Operations", "role": "Operations", "bio": "Ensures projects and support run on time."},
    ],
    Value: [
        {"title": "Integrity", "text": "We do what we promise."},
        {"title": "Innovation", "text": "We keep learning and improving."},
        {"title": "Excellence", "text": "Quality is our standard."},
        {"title": "Community", "text": "We train and employ local talent."},
    ],
    Milestone: [
        {"year": "Start", "title": "Founding", "text": "Started as a small IT repair and support shop in Abeokuta."},
        {"year": "Growth", "title": "Expansion", "text": "Expanded into networking and custom software for local businesses."},
        {"year": "Today", "title": "Full technology company", "text": "Serving schools, SMEs and public institutions."},
    ],
}


class Command(BaseCommand):
    help = "Adds sample content to empty tables. Replace it in the admin afterwards."

    def handle(self, *args, **options):
        SiteSettings.load()
        for model, rows in DATA.items():
            if model.objects.exists():
                self.stdout.write(f"{model.__name__}: already has content, skipped")
                continue
            for number, row in enumerate(rows, start=1):
                model.objects.create(order=number, **row)
            self.stdout.write(self.style.SUCCESS(f"{model.__name__}: added {len(rows)} sample rows"))
