from django.contrib import admin


class ShortIdAdminMixin:
    @admin.display(description="ID")
    def short_id(self, obj):
        if hasattr(obj, "id") and obj.id:
            return str(obj.id)[:8]
        return "—"
