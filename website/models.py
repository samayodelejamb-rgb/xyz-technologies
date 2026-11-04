from django.db import models

TOPICS = [
    "Software development",
    "Networking",
    "Cybersecurity",
    "IT support",
    "Products and hardware",
    "Other",
]


class PublishedManager(models.Manager):
    """Only returns items that are ticked 'published'."""

    def get_queryset(self):
        return super().get_queryset().filter(is_published=True)


class Orderable(models.Model):
    """Base for content that staff can reorder and hide from the admin."""

    order = models.PositiveSmallIntegerField(default=0, help_text="Lower numbers appear first.")
    is_published = models.BooleanField(default=True, help_text="Untick to hide from the website.")

    objects = models.Manager()
    published = PublishedManager()

    class Meta:
        abstract = True
        ordering = ["order", "id"]


class SiteSettings(models.Model):
    """One row only: company details used across the whole website."""

    company_name = models.CharField(max_length=120, default="XYZ Technologies Limited")
    tagline = models.CharField(
        max_length=200,
        default="Software, networks and smart business systems for Abeokuta and beyond.",
    )
    hero_title = models.CharField(max_length=200, default="Technology that moves Abeokuta and Nigeria forward.")
    hero_text = models.TextField(
        default="XYZ Technologies Limited designs software, networks and smart business systems "
                "for schools, businesses and government offices across Ogun State and beyond."
    )
    about_intro = models.TextField(
        default="XYZ Technologies Limited is a registered Nigerian technology company headquartered in "
                "Abeokuta, Ogun State. We help organisations adopt reliable, affordable digital tools."
    )
    mission = models.TextField(
        default="To deliver practical technology solutions that improve productivity, transparency "
                "and growth for our clients."
    )
    vision = models.TextField(default="To be the most trusted technology partner in South-West Nigeria.")

    phone = models.CharField(max_length=40, default="+234 800 000 0000")
    email = models.EmailField(default="info@xyztechnologies.com.ng")
    address = models.TextField(default="[Street address]\nAbeokuta, Ogun State\nNigeria")
    hours_weekdays = models.CharField(max_length=80, default="Mon to Fri: 8:00 am to 5:00 pm")
    hours_saturday = models.CharField(max_length=80, default="Sat: 9:00 am to 2:00 pm", blank=True)
    map_embed_url = models.URLField(
        blank=True,
        help_text="Google Maps > Share > Embed a map > copy the address inside src=\"...\".",
    )

    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)
    x_url = models.URLField("X (Twitter) URL", blank=True)

    class Meta:
        verbose_name = "Site settings"
        verbose_name_plural = "Site settings"

    def __str__(self):
        return "Site settings"

    def save(self, *args, **kwargs):
        self.pk = 1  # keep a single row
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class Stat(Orderable):
    value = models.CharField(max_length=20, help_text="For example: 150+")
    label = models.CharField(max_length=60)

    def __str__(self):
        return f"{self.value} {self.label}"


class Service(Orderable):
    icon = models.CharField(max_length=8, blank=True, help_text="One emoji, for example 💻")
    title = models.CharField(max_length=100)
    summary = models.CharField(max_length=220)

    def __str__(self):
        return self.title


class Product(Orderable):
    SOFTWARE = "software"
    HARDWARE = "hardware"
    CATEGORIES = [(SOFTWARE, "Software"), (HARDWARE, "Hardware")]

    category = models.CharField(max_length=10, choices=CATEGORIES, default=SOFTWARE)
    name = models.CharField(max_length=100)
    summary = models.CharField(max_length=220)
    includes = models.CharField(max_length=120, blank=True, help_text="Hardware only, for example: Installation")

    def __str__(self):
        return self.name


class Project(Orderable):
    sector = models.CharField(max_length=60, help_text="For example: Education")
    title = models.CharField(max_length=120)
    summary = models.CharField(max_length=240)

    def __str__(self):
        return self.title


class Testimonial(Orderable):
    quote = models.TextField()
    author = models.CharField(max_length=100)
    role = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.author


class TeamMember(Orderable):
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=100)
    bio = models.CharField(max_length=240, blank=True)

    def __str__(self):
        return f"{self.name}, {self.role}"


class Value(Orderable):
    title = models.CharField(max_length=60)
    text = models.CharField(max_length=160)

    def __str__(self):
        return self.title


class Milestone(Orderable):
    year = models.CharField(max_length=10, blank=True)
    title = models.CharField(max_length=80)
    text = models.CharField(max_length=240)

    def __str__(self):
        return self.title


class ContactMessage(models.Model):
    """A message sent from the Contact page."""

    NEW, READ, REPLIED = "new", "read", "replied"
    STATUSES = [(NEW, "New"), (READ, "Read"), (REPLIED, "Replied")]

    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=150)
    phone = models.CharField(max_length=30, blank=True)
    topic = models.CharField(max_length=50, choices=[(t, t) for t in TOPICS], default="Other")
    message = models.TextField()
    status = models.CharField(max_length=10, choices=STATUSES, default=NEW)

    created_at = models.DateTimeField(auto_now_add=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=300, blank=True)

    email_sent = models.BooleanField(default=False)
    email_error = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["ip", "created_at"])]

    def __str__(self):
        return f"{self.name} - {self.topic} ({self.created_at:%d %b %Y})"
