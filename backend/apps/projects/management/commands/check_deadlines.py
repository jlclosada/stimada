"""
Management command to run daily scheduled checks:
- Deadline reminders (3 days before delivery_deadline)
- Overdue delivery detection

Schedule via cron: python manage.py check_deadlines (daily)
"""
from django.core.management.base import BaseCommand

from apps.projects.services import check_deadline_reminders, check_overdue_deliveries


class Command(BaseCommand):
    help = "Check project deadlines: send reminders and mark overdue projects."

    def handle(self, *args, **options):
        self.stdout.write("Checking deadline reminders...")
        check_deadline_reminders()

        self.stdout.write("Checking overdue deliveries...")
        check_overdue_deliveries()

        self.stdout.write(self.style.SUCCESS("Done."))
