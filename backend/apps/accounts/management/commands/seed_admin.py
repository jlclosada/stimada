from django.core.management.base import BaseCommand

from apps.accounts.models import CustomUser


class Command(BaseCommand):
    help = "Crea el superusuario inicial de Stimada."

    def handle(self, *args, **options):
        email = "admin@stimada.com"
        if CustomUser.objects.filter(email=email).exists():
            self.stdout.write(self.style.WARNING(f"El administrador '{email}' ya existe."))
            return

        CustomUser.objects.create_superuser(
            email=email,
            password="Stimada2025!",
            full_name="Administrador Stimada",
        )
        self.stdout.write(self.style.SUCCESS(f"Superusuario '{email}' creado correctamente."))
