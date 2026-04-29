import csv
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

from django.core.management.base import BaseCommand

from apps.content_makers.models import ContentMakerProfile


def parse_bool(value: str) -> bool:
    return value.strip().upper() in ("TRUE", "SÍ", "SI", "1", "YES")


def parse_int(value: str) -> int | None:
    """Parse Spanish-formatted numbers: '2.480' → 2480."""
    v = value.strip().replace(".", "").replace(",", "").replace(" ", "")
    if not v or v == "-":
        return None
    try:
        return int(re.sub(r"[^\d]", "", v))
    except (ValueError, TypeError):
        return None


def parse_decimal(value: str) -> Decimal | None:
    v = value.strip().replace(",", ".").replace(" ", "")
    if not v or v == "-":
        return None
    try:
        return Decimal(re.sub(r"[^\d.]", "", v))
    except (InvalidOperation, TypeError):
        return None


def clean(value: str) -> str:
    return value.strip() if value else ""


class Command(BaseCommand):
    help = "Importa las content makers desde el CSV de Stimada."

    def add_arguments(self, parser):
        parser.add_argument(
            "--csv",
            default="/app/data/comunidad.csv",
            help="Ruta al fichero CSV",
        )
        parser.add_argument(
            "--update",
            action="store_true",
            help="Actualizar registros existentes en lugar de saltarlos",
        )

    def handle(self, *args, **options):
        csv_path = Path(options["csv"])
        if not csv_path.exists():
            self.stderr.write(self.style.ERROR(f"CSV no encontrado: {csv_path}"))
            return

        created = updated = skipped = errors = 0

        with open(csv_path, encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                stimada_id = clean(row.get("ID", ""))
                if not stimada_id:
                    errors += 1
                    continue

                defaults = {
                    "nombre": clean(row.get("Nombre", "")),
                    "apellidos": clean(row.get("Apellidos", "")),
                    "tipo_cm": clean(row.get("Tipo de CM", "")),
                    "sexo": clean(row.get("Sexo", "")),
                    "status": clean(row.get("Status", "")),
                    "desempeno": clean(row.get("Desempeño", "")),
                    "calidad_contenido": clean(row.get("Calidad del contenido", "")),
                    "apariencia": clean(row.get("Apariencia", "")),
                    "es_mama": parse_bool(row.get("Mamá", "")),
                    "categorias_contenido": clean(row.get("Contenido", "")),
                    "sigue_stimada": parse_bool(row.get("Siguen a @stimada", "")),
                    "stimada_en_bio": parse_bool(row.get("@stimada en bio", "")),
                    "contrato_firmado": parse_bool(row.get("Contrato Firmado", "")),
                    "fee_instagram": parse_decimal(row.get("Fee Instagram", "")),
                    "categoria_seguidores_ig": clean(row.get("Categorías # Seguidores Instagram", "")),
                    "seguidores_instagram": parse_int(row.get("Instagram Seguidores", "")),
                    "instagram_handle": clean(row.get("Instagram", "")),
                    "link_instagram": clean(row.get("Link Instagram", "")),
                    "fee_tiktok": parse_decimal(row.get("Fee Tiktok", "")),
                    "categoria_seguidores_tt": clean(row.get("Categorías # Seguidores TikTok", "")),
                    "seguidores_tiktok": parse_int(row.get("TikTok Seguidores", "")),
                    "tiktok_handle": clean(row.get("TikTok", "")),
                    "link_tiktok": clean(row.get("Link perfil Tik tok", "")),
                    "talla_arriba": clean(row.get("Tallaje: \nParte de Arriba", "")),
                    "talla_abajo": clean(row.get("Tallaje: \nParte de Abajo", "")),
                    "talla_pie": clean(row.get("Tallaje: \nPie", "")),
                    "altura_medidas": clean(row.get("Tallaje: \nAltura", "")),
                    "comentarios": clean(row.get("Comentarios", "")),
                    "email": clean(row.get("Mail", "")),
                    "telefono": clean(row.get("Teléfono", "")),
                    "direccion_facturacion": clean(row.get("Dirección de Facturación", "")),
                    "codigo_postal": clean(row.get("C.P.", "")),
                    "provincia": clean(row.get("Provincia", "")),
                    "pais": clean(row.get("País", "")),
                    "dni_cif": clean(row.get("DNI / CIF", "")),
                    "iban": clean(row.get("IBAN", "")),
                }

                try:
                    obj, was_created = ContentMakerProfile.objects.get_or_create(
                        stimada_id=stimada_id,
                        defaults=defaults,
                    )
                    if was_created:
                        created += 1
                    elif options["update"]:
                        for k, v in defaults.items():
                            setattr(obj, k, v)
                        obj.save()
                        updated += 1
                    else:
                        skipped += 1
                except Exception as exc:
                    self.stderr.write(f"Error en {stimada_id}: {exc}")
                    errors += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Importación completada — Creadas: {created} | Actualizadas: {updated} | "
                f"Saltadas: {skipped} | Errores: {errors}"
            )
        )
