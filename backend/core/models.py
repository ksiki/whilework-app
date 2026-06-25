import itertools

from django.db import models
from slugify import slugify
from unidecode import unidecode


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
            safe_name = (
                self.name.replace("+", "-plus-")
                .replace("#", "-sharp-")
                .replace(".", "-dot-")
            )

            original_slug = slugify(unidecode(safe_name))

            if not original_slug:
                original_slug = "item"

            unique_slug = original_slug
            ModelClass = self.__class__

            for x in itertools.count(1):
                if not ModelClass.objects.filter(slug=unique_slug).exists():
                    break
                unique_slug = f"{original_slug}-{x}"

            self.slug = unique_slug

        super().save(*args, **kwargs)
