from django.conf import settings
from django.db import models


class ClientType(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Client type"
        verbose_name_plural = "Client types"
        ordering = ["order", "name"]

    def __str__(self):
        return self.name


class ClientProfile(models.Model):
    # User account
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="client_profile",
    )

    # Identification
    name = models.CharField(max_length=200, verbose_name="Commercial name")
    client_id = models.CharField(max_length=50, unique=True, blank=True)
    client_type = models.ForeignKey(
        ClientType,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="clients",
    )
    web_instagram = models.URLField(max_length=300, blank=True, verbose_name="Web / Instagram")

    # Contact
    contact_person = models.CharField(max_length=200, blank=True, verbose_name="Contact person")
    contact_email = models.EmailField(blank=True, verbose_name="Contact email")
    phone = models.CharField(max_length=30, blank=True)

    # Billing
    billing_name = models.CharField(max_length=200, verbose_name="Legal name")
    cif = models.CharField(max_length=20)
    billing_email = models.EmailField()
    billing_address = models.TextField()
    postal_code = models.CharField(max_length=10)
    city = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default="España")

    # Contract
    contract_signed = models.BooleanField(default=False)
    contract = models.FileField(upload_to="contratos/clientes/", null=True, blank=True)

    # Status and evaluation
    STATUS_ACTIVE = "activo"
    STATUS_INACTIVE = "inactivo"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Activo"),
        (STATUS_INACTIVE, "Inactivo"),
    ]
    TRAFFIC_LIGHT_CHOICES = [(1, "1"), (2, "2"), (3, "3")]

    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default=STATUS_ACTIVE
    )
    traffic_light = models.PositiveSmallIntegerField(
        choices=TRAFFIC_LIGHT_CHOICES, null=True, blank=True,
        verbose_name="Client traffic light",
    )
    internal_notes = models.TextField(blank=True, verbose_name="Internal notes")

    # Agency / Brand
    is_agency = models.BooleanField(
        default=False,
        help_text="If it is an agency, it can have multiple associated brands.",
    )

    # Favorite content makers
    favorite_cms = models.ManyToManyField(
        "content_makers.ContentMakerProfile",
        blank=True,
        related_name="favorited_by_clients",
    )

    # Metadata
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="created_clients",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        ordering = ["name"]

    @staticmethod
    def generate_next_id():
        """Generate the next sequential numeric client ID (zero-padded to 5 digits)."""
        import re
        ids = ClientProfile.objects.values_list("client_id", flat=True)
        nums = [int(m.group()) for cid in ids if (m := re.search(r"\d+", cid))]
        next_num = (max(nums) if nums else 0) + 1
        return f"{next_num:05d}"

    def save(self, *args, **kwargs):
        if not self.client_id:
            self.client_id = self.generate_next_id()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.client_id} — {self.name}"


class Brand(models.Model):
    """Brand associated with a client (agency). If the client is an own brand, a brand with the same name is created."""
    STATUS_ACTIVE = "activa"
    STATUS_INACTIVE = "inactiva"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Activa"),
        (STATUS_INACTIVE, "Inactiva"),
    ]

    brand_id = models.CharField(max_length=50, unique=True, blank=True)
    client = models.ForeignKey(
        ClientProfile,
        on_delete=models.CASCADE,
        related_name="brands",
    )
    name = models.CharField(max_length=200, verbose_name="Brand name")
    brand_type = models.ForeignKey(
        ClientType,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="brands",
        verbose_name="Brand type",
    )
    web_instagram = models.URLField(max_length=300, blank=True, verbose_name="Web / Instagram")
    notes = models.TextField(blank=True)

    # Brand's own contact (if empty, inherits from client)
    contact_person = models.CharField(max_length=200, blank=True, verbose_name="Contact person")
    contact_email = models.EmailField(blank=True, verbose_name="Contact email")
    phone = models.CharField(max_length=30, blank=True, verbose_name="Phone")

    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default=STATUS_ACTIVE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Brand"
        verbose_name_plural = "Brands"
        ordering = ["name"]
        unique_together = ["client", "name"]

    @staticmethod
    def generate_next_id():
        """Generate the next sequential brand ID (zero-padded to 5 digits)."""
        import re
        ids = Brand.objects.values_list("brand_id", flat=True)
        nums = [int(m.group()) for bid in ids if (m := re.search(r"\d+", bid))]
        next_num = (max(nums) if nums else 0) + 1
        return f"{next_num:05d}"

    def save(self, *args, **kwargs):
        if not self.brand_id:
            self.brand_id = self.generate_next_id()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.client.name})"
