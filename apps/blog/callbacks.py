import json
from typing import Any

from django.conf import settings
from django.db.models import Count, Q
from django.http import HttpRequest
from django.urls import reverse_lazy

from apps.auths.models import User
from apps.blog.models import Category, Comment, Post

TOP_AUTHOR_LIMIT = 5


def environment_callback(request: HttpRequest):
    """Return environmental status and status"""
    if settings.ENV_ID == "prod":
        return "Production", "danger"
    return "Local", "warning"


def drafts_badge(request: HttpRequest) -> str:
    """Return total number of drafts."""
    count = Post.objects.filter(status=Post.StatusType.DRAFT).count()
    return str(count)


def sidebar_navigation(request: HttpRequest) -> list[dict[str, Any]]:
    """Return custom sidebar navigation structure."""
    return [
        {
            "title": "Overview",
            "items": [
                {
                    "title": "Dashboard",
                    "icon": "dashboard",
                    "link": reverse_lazy("admin:index"),
                },
            ],
        },
        {
            "title": "Content",
            "items": [
                {
                    "title": "Posts",
                    "icon": "article",
                    "link": reverse_lazy("admin:blog_post_changelist"),
                    "badge": "apps.blog.callbacks.drafts_badge",
                },
                {
                    "title": "Comments",
                    "icon": "chat_bubble",
                    "link": reverse_lazy("admin:blog_comment_changelist"),
                },
                {
                    "title": "Categories",
                    "icon": "category",
                    "link": reverse_lazy("admin:blog_category_changelist"),
                },
                {
                    "title": "Tags",
                    "icon": "sell",
                    "link": reverse_lazy("admin:blog_tag_changelist"),
                },
            ],
        },
        {
            "title": "Users & Access",
            "items": [
                {
                    "title": "Users",
                    "icon": "group",
                    "link": reverse_lazy("admin:auths_user_changelist"),
                    "permission": lambda request: request.user.is_superuser,
                },
                {
                    "title": "Groups",
                    "icon": "groups",
                    "link": reverse_lazy("admin:auth_group_changelist"),
                    "permission": lambda request: request.user.is_superuser,
                },
            ],
        },
    ]


def dashboard_callback(request: HttpRequest, context: dict[str, Any]) -> dict[str, Any]:
    """Populate the admin dashboard with blog statistics."""
    post_counts = Post.objects.aggregate(
        published=Count("pk", filter=Q(status=Post.StatusType.PUBLISHED)),
        drafts=Count("pk", filter=Q(status=Post.StatusType.DRAFT)),
    )
    published = post_counts["published"]
    drafts = post_counts["drafts"]
    total_posts = published + drafts
    published_share = round(published * 100 / total_posts) if total_posts else 0
    draft_share = 100 - published_share if total_posts else 0

    categories = list(
        Category.objects.annotate(posts_total=Count("post"))
        .order_by("-posts_total", "name")
        .values_list("name", "posts_total")
    )
    authors = (
        User.objects.annotate(posts_total=Count("post"))
        .filter(posts_total__gt=0)
        .order_by("-posts_total", "pk")[:TOP_AUTHOR_LIMIT]
    )

    context.update(
        cards=[
            {"title": "Total users", "value": User.objects.count(), "icon": "group"},
            {"title": "Published posts", "value": published, "icon": "check_circle"},
            {"title": "Draft posts", "value": drafts, "icon": "edit_note"},
            {
                "title": "Total comments",
                "value": Comment.objects.count(),
                "icon": "chat_bubble",
            },
        ],
        category_counts=categories,
        posts_per_category_chart=json.dumps(
            {
                "labels": [name for name, _ in categories],
                "datasets": [
                    {
                        "label": "Posts",
                        "data": [count for _, count in categories],
                        "backgroundColor": "var(--color-primary-600)",
                        "borderRadius": 5,
                        "maxBarThickness": 18,
                    }
                ],
            }
        ),
        category_chart_options=json.dumps(
            {
                "indexAxis": "y",
                "maintainAspectRatio": False,
                "plugins": {"legend": {"display": False}},
                "scales": {
                    "x": {
                        "beginAtZero": True,
                        "suggestedMax": 1,
                        "ticks": {"precision": 0, "color": "#858b94"},
                        "border": {"display": False, "dash": [4, 4]},
                    },
                    "y": {
                        "ticks": {"color": "#858b94"},
                        "grid": {"display": False},
                        "border": {"display": False},
                    },
                },
            }
        ),
        top_authors={
            "headers": [
                "Rank",
                "Author",
                {"content": "Posts", "class": "dashboard-count"},
            ],
            "rows": [
                [
                    rank,
                    f"{author.first_name} {author.last_name}".strip()
                    or "Unnamed author",
                    {"content": author.posts_total, "class": "dashboard-count"},
                ]
                for rank, author in enumerate(authors, start=1)
            ],
        },
        status_progress=[
            {
                "title": "Published",
                "value": published_share,
                "count": published,
                "bars": [
                    {"value": published_share, "progress_class": "dashboard-fill"}
                ],
            },
            {
                "title": "Drafts",
                "value": draft_share,
                "count": drafts,
                "bars": [
                    {
                        "value": draft_share,
                        "progress_class": "dashboard-fill dashboard-drafts",
                    }
                ],
            },
        ],
        total_posts=total_posts,
    )
    return context
