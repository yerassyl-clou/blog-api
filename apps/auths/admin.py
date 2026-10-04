from django.contrib import admin

from apps.auths.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Custom user model admin configuration class."""
    



