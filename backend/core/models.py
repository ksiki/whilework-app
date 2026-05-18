from django.db import models
from django.utils.text import slugify


class TimeStampedMixin(models.Model):
    """
    Automatically creates created_at and updated_at fields
    """

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SluggedMixin(models.Model):
    """
    Automatically creates the name and slug fields. slug - created from the name via slugify
    """

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs) -> None:
        if self.name and not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
