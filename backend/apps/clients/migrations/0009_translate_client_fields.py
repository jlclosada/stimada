from django.conf import settings
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('clients', '0008_add_brand_contact_fields'),
    ]

    operations = [
        # --- ClientType ---
        migrations.RenameField(model_name='clienttype', old_name='nombre', new_name='name'),
        migrations.RenameField(model_name='clienttype', old_name='activo', new_name='is_active'),
        migrations.RenameField(model_name='clienttype', old_name='orden', new_name='order'),
        migrations.AlterModelOptions(
            name='clienttype',
            options={'ordering': ['order', 'name'], 'verbose_name': 'Client type', 'verbose_name_plural': 'Client types'},
        ),

        # --- ClientProfile ---
        migrations.RenameField(model_name='clientprofile', old_name='nombre_cliente', new_name='name'),
        migrations.RenameField(model_name='clientprofile', old_name='cliente_id', new_name='client_id'),
        migrations.RenameField(model_name='clientprofile', old_name='tipo_cliente', new_name='client_type'),
        migrations.RenameField(model_name='clientprofile', old_name='persona_contacto', new_name='contact_person'),
        migrations.RenameField(model_name='clientprofile', old_name='email_contacto', new_name='contact_email'),
        migrations.RenameField(model_name='clientprofile', old_name='telefono', new_name='phone'),
        migrations.RenameField(model_name='clientprofile', old_name='nombre_facturacion', new_name='billing_name'),
        migrations.RenameField(model_name='clientprofile', old_name='email_facturacion', new_name='billing_email'),
        migrations.RenameField(model_name='clientprofile', old_name='direccion_facturacion', new_name='billing_address'),
        migrations.RenameField(model_name='clientprofile', old_name='codigo_postal', new_name='postal_code'),
        migrations.RenameField(model_name='clientprofile', old_name='ciudad', new_name='city'),
        migrations.RenameField(model_name='clientprofile', old_name='pais', new_name='country'),
        migrations.RenameField(model_name='clientprofile', old_name='contrato_firmado', new_name='contract_signed'),
        migrations.RenameField(model_name='clientprofile', old_name='contrato', new_name='contract'),
        migrations.RenameField(model_name='clientprofile', old_name='estado', new_name='status'),
        migrations.RenameField(model_name='clientprofile', old_name='semaforo_cliente', new_name='traffic_light'),
        migrations.RenameField(model_name='clientprofile', old_name='notas_internas', new_name='internal_notes'),
        migrations.RenameField(model_name='clientprofile', old_name='es_agencia', new_name='is_agency'),
        migrations.AlterModelOptions(
            name='clientprofile',
            options={'ordering': ['name'], 'verbose_name': 'Client', 'verbose_name_plural': 'Clients'},
        ),
        migrations.AlterField(
            model_name='clientprofile',
            name='client_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='clients', to='clients.clienttype'),
        ),
        migrations.AlterField(
            model_name='clientprofile',
            name='created_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_clients', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='clientprofile',
            name='name',
            field=models.CharField(max_length=200, verbose_name='Commercial name'),
        ),
        migrations.AlterField(
            model_name='clientprofile',
            name='billing_name',
            field=models.CharField(max_length=200, verbose_name='Legal name'),
        ),
        migrations.AlterField(
            model_name='clientprofile',
            name='contact_person',
            field=models.CharField(blank=True, max_length=200, verbose_name='Contact person'),
        ),
        migrations.AlterField(
            model_name='clientprofile',
            name='contact_email',
            field=models.EmailField(blank=True, max_length=254, verbose_name='Contact email'),
        ),
        migrations.AlterField(
            model_name='clientprofile',
            name='traffic_light',
            field=models.PositiveSmallIntegerField(blank=True, choices=[(1, '1'), (2, '2'), (3, '3')], null=True, verbose_name='Client traffic light'),
        ),
        migrations.AlterField(
            model_name='clientprofile',
            name='internal_notes',
            field=models.TextField(blank=True, verbose_name='Internal notes'),
        ),
        migrations.AlterField(
            model_name='clientprofile',
            name='is_agency',
            field=models.BooleanField(default=False, help_text='If it is an agency, it can have multiple associated brands.'),
        ),

        # --- Brand ---
        migrations.RenameField(model_name='brand', old_name='nombre', new_name='name'),
        migrations.RenameField(model_name='brand', old_name='tipo_marca', new_name='brand_type'),
        migrations.RenameField(model_name='brand', old_name='notas', new_name='notes'),
        migrations.RenameField(model_name='brand', old_name='persona_contacto', new_name='contact_person'),
        migrations.RenameField(model_name='brand', old_name='email_contacto', new_name='contact_email'),
        migrations.RenameField(model_name='brand', old_name='telefono', new_name='phone'),
        migrations.RenameField(model_name='brand', old_name='estado', new_name='status'),
        migrations.AlterModelOptions(
            name='brand',
            options={'ordering': ['name'], 'verbose_name': 'Brand', 'verbose_name_plural': 'Brands'},
        ),
        migrations.AlterUniqueTogether(
            name='brand',
            unique_together={('client', 'name')},
        ),
        migrations.AlterField(
            model_name='brand',
            name='brand_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='brands', to='clients.clienttype', verbose_name='Brand type'),
        ),
        migrations.AlterField(
            model_name='brand',
            name='name',
            field=models.CharField(max_length=200, verbose_name='Brand name'),
        ),
        migrations.AlterField(
            model_name='brand',
            name='contact_person',
            field=models.CharField(blank=True, max_length=200, verbose_name='Contact person'),
        ),
        migrations.AlterField(
            model_name='brand',
            name='contact_email',
            field=models.EmailField(blank=True, max_length=254, verbose_name='Contact email'),
        ),
        migrations.AlterField(
            model_name='brand',
            name='phone',
            field=models.CharField(blank=True, max_length=30, verbose_name='Phone'),
        ),
    ]
