from django.contrib import admin
from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.db.models import Count, QuerySet
from django.http import HttpRequest
from unfold.admin import ModelAdmin
from unfold.contrib.filters.admin import BooleanRadioFilter
from unfold.decorators import action, display
from unfold.forms import (
    AdminPasswordChangeForm,
    UserChangeForm,
    UserCreationForm,
)

from apps.auths.models import User


class BlogUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("email", "first_name", "last_name")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields.pop("usable_password", None)
        self.fields["password1"].required = True
        self.fields["password2"].required = True


class BlogUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = "__all__"


@admin.register(User)
class UserAdmin(BaseUserAdmin, ModelAdmin):
    """Custom user model admin configuration class."""

    form = BlogUserChangeForm
    add_form = BlogUserCreationForm
    change_password_form = AdminPasswordChangeForm

    ordering = ("email",)
    search_fields = ("email", "first_name", "last_name")
    actions = ("activate_users", "deactivate_users")
    readonly_fields = ("last_login",)

    list_filter = (
        ("is_active", BooleanRadioFilter),
        ("is_staff", BooleanRadioFilter),
    )

    list_display = (
        "user_header",
        "post_count",
        "active_label",
        "staff_label",
    )

    fieldsets = (
        (
            "Personal info",
            {
                "classes": ("tab",),
                "fields": ("email", "first_name", "last_name", "password"),
            },
        ),
        (
            "Permissions",
            {
                "classes": ("tab",),
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                ),
            },
        ),
        (
            "Important dates",
            {
                "classes": ("tab",),
                "fields": ("last_login",),
            },
        ),
    )

    add_fieldsets = (
        (
            "Account information",
            {
                "fields": (
                    "email",
                    "first_name",
                    "last_name",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    def get_queryset(self, request: HttpRequest) -> QuerySet[User]:
        return (
            super()
            .get_queryset(request)
            .annotate(posts_total=Count("post", distinct=True))
        )

    @display(description="User", header=True, ordering="first_name")
    def user_header(self, obj: User) -> tuple[str, str, str]:
        name = f"{obj.first_name} {obj.last_name}"
        initials = f"{obj.first_name[:1]} {obj.last_name[:1]}".upper()
        return name, obj.email, initials

    @display(description="Posts", ordering="posts_total")
    def post_count(self, obj: User) -> int:
        return obj.posts_total

    @display(description="Active", label={True: "success", False: "danger"})
    def active_label(self, obj: User) -> tuple[bool, str]:
        return obj.is_active, "Active" if obj.is_active else "Inactive"

    @display(description="Staff", label={True: "info", False: "warning"})
    def staff_label(self, obj: User) -> tuple[bool, str]:
        return obj.is_staff, "Staff" if obj.is_staff else "Regular"

    @action(description="Activate selected", permissions=["change"])
    def activate_users(self, request: HttpRequest, queryset: QuerySet[User]) -> None:
        changed = queryset.update(is_active=True)
        self.message_user(request, f"Activated {changed} users")

    @action(description="Deactivate selected", permissions=["change"])
    def deactivate_users(self, request: HttpRequest, queryset: QuerySet[User]) -> None:
        changed = queryset.exclude(pk=request.user.pk).update(is_active=False)
        self.message_user(request, f"Deactivated {changed} users")


admin.site.unregister(Group)


@admin.register(Group)
class GroupAdmin(BaseGroupAdmin, ModelAdmin):
    """Custom group admin configuration class."""
