from typing import ClassVar

from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Prefetch, QuerySet, TextField
from django.db.models.functions import Now
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.text import Truncator
from unfold.admin import ModelAdmin, TabularInline
from unfold.contrib.filters.admin import (
    AutocompleteSelectFilter,
    ChoicesDropdownFilter,
    MultipleRelatedDropdownFilter,
    RangeDateTimeFilter,
    RelatedDropdownFilter,
)
from unfold.contrib.forms.widgets import WysiwygWidget
from unfold.decorators import action, display
from unfold.sections import TableSection

from apps.blog.forms import PostAdminForm
from apps.blog.models import Category, Comment, Post, Tag

COMMENT_PREVIEW_LENGTH = 80
COMMENTS_PER_PAGE = 10


class CategoryPostSection(TableSection):
    verbose_name = "Posts in category"
    related_name = "post_set"
    fields = ("title", "status", "author")


class PostCommentSection(TableSection):
    verbose_name = "Comments on post"
    related_name = "comment_set"
    fields = ("author", "body", "created_at")


@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    search_fields = ("name",)
    prepopulated_fields: ClassVar = {"slug": ("name",)}
    list_display = ("name", "post_count")
    list_sections = (CategoryPostSection,)

    def get_queryset(self, request: HttpRequest) -> QuerySet[Category]:
        return (
            super()
            .get_queryset(request)
            .annotate(posts_total=Count("post"))
            .prefetch_related(
                Prefetch("post_set", queryset=Post.objects.select_related("author"))
            )
        )

    @display(description="Posts", ordering="posts_total")
    def post_count(self, obj: Category) -> int:
        return obj.posts_total


@admin.register(Tag)
class TagAdmin(ModelAdmin):
    list_display = ("name", "post_count")
    search_fields = ("name",)
    prepopulated_fields: ClassVar = {"slug": ("name",)}

    def get_queryset(self, request: HttpRequest) -> QuerySet[Tag]:
        return super().get_queryset(request).annotate(posts_total=Count("post"))

    @display(description="Posts", ordering="posts_total")
    def post_count(self, obj: Tag) -> int:
        return obj.posts_total


class CommentInline(TabularInline):
    model = Comment
    fields = ("author", "body", "created_at")
    readonly_fields = ("created_at",)
    autocomplete_fields = ("author",)
    tab = True
    per_page = COMMENTS_PER_PAGE
    extra = 0

    def get_queryset(self, request: HttpRequest) -> QuerySet[Comment]:
        return (
            super()
            .get_queryset(request)
            .select_related("author")
            .order_by("-created_at", "-pk")
        )


@admin.register(Post)
class PostAdmin(ModelAdmin):
    form = PostAdminForm
    list_display = (
        "post_header",
        "status_label",
        "category",
        "tags_dropdown",
        "comment_count",
        "created_at",
    )
    search_fields = ("title", "body", "author__email")
    list_filter = (
        ("status", ChoicesDropdownFilter),
        ("category", RelatedDropdownFilter),
        ("tags", MultipleRelatedDropdownFilter),
        ("author", AutocompleteSelectFilter),
        ("created_at", RangeDateTimeFilter),
    )
    list_filter_submit = True
    list_filter_sheet = False
    list_sections = (PostCommentSection,)

    actions = ("publish_selected", "move_selected_to_drafts")
    actions_row = ("publish_post", "unpublish_post")
    actions_list = ("publish_all_drafts",)
    actions_detail = ("open_comments",)
    actions_submit_line = ("save_and_publish",)

    fieldsets = (
        ("Content", {"classes": ("tab",), "fields": ("title", "slug", "body")}),
        (
            "Classification",
            {"classes": ("tab",), "fields": ("category", "tags", "status")},
        ),
        (
            "Meta",
            {"classes": ("tab",), "fields": ("author", "created_at", "updated_at")},
        ),
    )
    prepopulated_fields: ClassVar = {"slug": ("title",)}
    autocomplete_fields = ("author", "category", "tags")
    formfield_overrides: ClassVar = {TextField: {"widget": WysiwygWidget}}
    readonly_fields = ("created_at", "updated_at")
    inlines = (CommentInline,)
    warn_unsaved_form = True

    @display(description="Post", header=True, ordering="title")
    def post_header(self, obj: Post) -> tuple[str, str]:
        return obj.title, obj.author.email

    @display(
        description="Status",
        ordering="status",
        label={Post.StatusType.PUBLISHED: "success", Post.StatusType.DRAFT: "warning"},
    )
    def status_label(self, obj: Post) -> tuple[str, str]:
        return obj.status, obj.get_status_display()

    @display(description="Tags", dropdown=True)
    def tags_dropdown(self, obj: Post) -> dict[str, str | list[dict[str, str]]]:
        tags = list(obj.tags.all())
        return {
            "title": f"Tags ({len(tags)})",
            "items": [{"title": tag.name} for tag in tags],
        }

    @display(description="Comments", ordering="comments_total")
    def comment_count(self, obj: Post) -> int:
        return obj.comments_total

    def get_queryset(self, request: HttpRequest) -> QuerySet[Post]:
        return (
            super()
            .get_queryset(request)
            .select_related("author", "category")
            .annotate(comments_total=Count("comment", distinct=True))
            .prefetch_related(
                "tags",
                Prefetch(
                    "comment_set", queryset=Comment.objects.select_related("author")
                ),
            )
        )

    def _set_status(
        self, request: HttpRequest, queryset: QuerySet[Post], status: Post.StatusType
    ) -> None:
        changed = queryset.exclude(status=status).update(
            status=status, updated_at=Now()
        )
        self.message_user(request, f"Posts moved to {status.label.lower()}: {changed}.")

    def _action_post(self, request: HttpRequest, object_id: str) -> Post:
        post = self.get_object(request, object_id)
        if post is None:
            raise Http404
        return post

    def _change_post_status(
        self, request: HttpRequest, object_id: str, status: Post.StatusType
    ) -> HttpResponse:
        post = self._action_post(request, object_id)
        if not self.has_change_permission(request, post):
            raise PermissionDenied
        self._set_status(request, Post.objects.filter(pk=post.pk), status)
        return self._after_list_action(request)

    def _after_list_action(self, request: HttpRequest) -> HttpResponse:
        url = reverse("admin:blog_post_changelist")
        if request.headers.get("HX-Request") == "true":
            return HttpResponse(headers={"HX-Redirect": url})
        return redirect(url)

    @action(description="Publish selected", permissions=["change"])
    def publish_selected(self, request: HttpRequest, queryset: QuerySet[Post]) -> None:
        self._set_status(request, queryset, Post.StatusType.PUBLISHED)

    @action(description="Move selected to drafts", permissions=["change"])
    def move_selected_to_drafts(
        self, request: HttpRequest, queryset: QuerySet[Post]
    ) -> None:
        self._set_status(request, queryset, Post.StatusType.DRAFT)

    @action(
        description="Publish this post",
        permissions=["change"],
        dialog={"title": "Publish this post?", "form_submit_text": "Publish"},
    )
    def publish_post(self, request: HttpRequest, form, object_id: str) -> HttpResponse:
        return self._change_post_status(request, object_id, Post.StatusType.PUBLISHED)

    @action(
        description="Unpublish this post",
        permissions=["change"],
        dialog={
            "title": "Move this post to drafts?",
            "form_submit_text": "Move to drafts",
        },
    )
    def unpublish_post(
        self, request: HttpRequest, form, object_id: str
    ) -> HttpResponse:
        return self._change_post_status(request, object_id, Post.StatusType.DRAFT)

    @action(
        description="Publish all drafts",
        permissions=["change"],
        dialog={"title": "Publish all drafts?", "form_submit_text": "Publish all"},
    )
    def publish_all_drafts(self, request: HttpRequest, form) -> HttpResponse:
        drafts = Post.objects.filter(status=Post.StatusType.DRAFT)
        self._set_status(request, drafts, Post.StatusType.PUBLISHED)
        return self._after_list_action(request)

    @action(description="Open this post's comments", permissions=["blog.view_comment"])
    def open_comments(
        self, request: HttpRequest, object_id: str
    ) -> HttpResponseRedirect:
        post = self._action_post(request, object_id)
        if not self.has_view_or_change_permission(request, post):
            raise PermissionDenied
        return redirect(
            reverse("admin:blog_comment_changelist", query={"post__id__exact": post.pk})
        )

    @action(description="Save & publish", permissions=["change"])
    def save_and_publish(self, request: HttpRequest, obj: Post) -> None:
        if obj.status != Post.StatusType.PUBLISHED:
            obj.status = Post.StatusType.PUBLISHED
            obj.save(update_fields=["status", "updated_at"])


@admin.register(Comment)
class CommentAdmin(ModelAdmin):
    list_display = ("post_title", "author", "body_preview", "created_at")
    search_fields = ("body", "author__email", "post__title")
    autocomplete_fields = ("post", "author")
    list_select_related = ("post", "author")
    readonly_fields = ("created_at",)
    list_filter = (
        ("post", AutocompleteSelectFilter),
        ("author", AutocompleteSelectFilter),
        ("created_at", RangeDateTimeFilter),
    )
    list_filter_submit = True

    @display(description="Post", ordering="post__title")
    def post_title(self, obj: Comment) -> str:
        return obj.post.title

    @display(description="Body")
    def body_preview(self, obj: Comment) -> str:
        return Truncator(obj.body).chars(COMMENT_PREVIEW_LENGTH)
