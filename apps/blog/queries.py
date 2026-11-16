from datetime import date, timedelta
from typing import Any

from django.db import transaction
from django.db.models import (
    Avg,
    Case,
    CharField,
    Count,
    Exists,
    F,
    Max,
    Min,
    OuterRef,
    Prefetch,
    Q,
    QuerySet,
    Subquery,
    Value,
    When,
)
from django.db.models.functions import Coalesce, Concat, TruncMonth
from django.utils import timezone
from django.utils.text import slugify

from apps.auths.models import User
from apps.blog.models import Category, Comment, Post, Tag

NEWEST_PUBLISHED_LIMIT = 5
POSTS_PER_PAGE = 10
MIN_HOURS_AFTER_CREATION = 1
UNCATECORIZED_LABEL="Uncategorized"
AVG_DECIMALS = 2
TOP_AUTHORS_LIMIT = 5

HOT_COMMENTS_MIN = 10
NORMAL_COMMENTS_MIN = 3
HOT_LABEL = "hot"
NORMAL_LABEL = "normal"
QUIET_LABEL = "quiet "

PUBLISHED_LIMIT = 50
NEWEST_POSTS_WITH_TAGS_LIMIT = 20

#Level 1
def categories_by_name() -> QuerySet[Category]:
    """All categories, sorted by name."""
    return Category.objects.order_by("name")

def published_posts() -> QuerySet[Post]:
    """Return published posts, newest first."""
    return Post.objects.filter(status=Post.StatusType.PUBLISHED).order_by("created_at")

def newest_published_posts() -> QuerySet[Post]:
    """Return 5 newest published posts."""
    return published_posts()[:NEWEST_PUBLISHED_LIMIT]

def post_by_slug(slug:str) -> Post | None:
    """Return post with this slug."""
    return Post.objects.filter(slug=slug)

def active_users_count() -> int:
    """Return number of active user."""
    return User.objects.filter(is_active=True, is_staff=False).count()

def has_drafts() -> bool: 
    """Is there at least one draft post."""
    return Post.objects.filter(status=Post.StatusType.DRAFT).exists()

def published_posts_page(page: int) -> QuerySet[Post]:
    """Return one page of published posts"""
    start = (page - 1) * POSTS_PER_PAGE
    end = start + POSTS_PER_PAGE
    return published_posts()[start:end]
     

# Level 2

def posts_with_word_in_title(word: str) -> QuerySet[Post]:
    """Return posts whose title contains word."""
    return Post.objects.filter(title__contains=word)


def users_with_email_domain(domain: str) -> QuerySet[User]:
    """Return categories whose slug is in the list slugs"""
    return User.objects.filter(email__iendswith=f"@{domain}")


def posts_without_category() -> QuerySet[Post]:
    """Return posts without categories."""
    return Post.objects.filter(category__isnull=True)


def categories_by_slugs(slugs: list[str]) -> QuerySet[Category]:
    """Return categories whose slug is in the list."""
    return Category.objects.filter(slug__in=slugs)


def posts_in_month(year: int, month: int) -> QuerySet[Post]:
    """Return posts created in this month of this year"""
    return Post.objects.filter(created_at__year=year, created_at__month=month)


def posts_last_days(days: int) -> QuerySet[Post]:
    """Return posts created in the last x days"""
    difference = timezone.now() - timedelta(days=days)
    return Post.objects.filter(created_at__gte=difference)


def posts_between(start: date, end: date) -> QuerySet[Post]:
    """Return posts from start through end, inclusive of both dates."""
    return Post.objects.filter(created_at__date__range=(start, end))


# Level 3

def author_published_posts(email: str) -> QuerySet[Post]:
    """Return published posts by author with given email."""
    return Post.objects.filter(
        author__email__iexact=email,
        status=Post.StatusType.PUBLISHED
    )


def posts_with_tag(tag_slug: str) -> QuerySet[Post]:
    """Return posts containing the tag identified by slug."""
    return Post.objects.filter(tags__slug=tag_slug)


def comments_in_category(category_slug: str) -> QuerySet[Comment]:
    """Return comments on posts in the requested category."""
    return Comment.objects.filter(post__category__slug=category_slug)



def users_with_published_posts() -> QuerySet[User]:
    """Return users who have at least one published post."""
    return User.objects.filter(
        post__status=Post.StatusType.PUBLISHED
    ).distinct()


def posts_without_tags() -> QuerySet[Post]:
    """Return posts that have no tags."""
    return Post.objects.filter(tags__isnull=True)


def users_without_comments() -> QuerySet[User]:
    """Return users wothout comments."""
    return User.objects.filter(comment__isnull=True)


def posts_with_both_tags(first_slug: str, second_slug: str) -> QuerySet[Post]:
    """Return posts that contain both requested tags."""
    return (
        Post.objects.filter(tags__slug=first_slug)
        .filter(tags__slug=second_slug)
        .distinct()
    )


# Level 4

def search_posts(text: str) -> QuerySet[Post]:
    """Return posts that have text in the title or in the body."""
    return Post.objects.filter(
        Q(title__icontains=text) | Q(body__icontains=text)
    )


def published_posts_missing_info() -> QuerySet[Post]:
    """Return published posts that have no category or no tags."""
    return Post.objects.filter(
        status=Post.StatusType.PUBLISHED
    ).filter(
        Q(category__isnull=True) | Q(category__isnull=True)
    ).distinct()


def edited_posts() -> QuerySet[Post]:
    """Return posts edited more than 1 hour after creation."""
    return Post.objects.filter(
        updated_at__gt=F("created_at") + timedelta(hours=MIN_HOURS_AFTER_CREATION)
    )


def comments_by_post_author() -> QuerySet[Comment]:
    """Return comments that the author of the post wrote under their own post"""
    return Comment.objects.filter(
        author_id=F("post__author_id")
    )


def comments_before_post() -> QuerySet[Comment]:
    """Return comments created before their post"""
    return Comment.objects.filter(
        created_at__lt=F("post__created_at")
    )


# Level 5

def published_authors_emails() -> list[str]:
    """Return mails of authors who have published posts"""
    return User.objects.filter(
        post__status=Post.StatusType.PUBLISHED
    ).order_by("email").values_list("email", flat=True).distinct()


def published_posts_overview() -> list[dict[str, Any]]:
    """Return title, author_email category_name for published posts"""
    return list(
        Post.objects.filter(status=Post.StatusType.PUBLISHED).values(
            "title",
            author_email=F("author__email"),
            category__name = Coalesce("category__name", Value(UNCATECORIZED_LABEL))
        )
    )


# Level 6

def posts_stats() -> dict[str, Any]:
    """Return post counts and first and last creation dates."""
    return Post.objects.aggregate(
        total=Count("pk"),
        published=Count(
            "pk", filter=Q(status=Post.StatusType.PUBLISHED)
        ),
        drafts=Count("pk", filter=Q(status=Post.StatusType.DRAFT)),
        first_post_at=Min("created_at"),
        last_post_at=Max("created_at"),
    )


def average_comments_per_post() -> float:
    """Return average comments per published post, including zeros."""

    avg = (
        Post.objects.filter(status=Post.StatusType.PUBLISHED)
        .annotate(comment_count=Count("comment"))
        .aggregate(value=Avg("comment_count"))
    )["value"]
    return round(avg or 0.0, AVG_DECIMALS)


# Level 7

def categories_with_post_count() -> QuerySet[Category]:
    """Return categories with post counts, largest first."""
    return Category.objects.annotate(
        post_count=Count("post")
    ).order_by("-post_count", "name")


def categories_with_published_count() -> QuerySet[Category]:
    """Return every category with its number of published posts."""
    return Category.objects.annotate(
        published_count=Count(
            "post", filter=Q(post__status=Post.StatusType.PUBLISHED)
        )
    )


def top_authors() -> QuerySet[User]:
    """Return five authors with most published posts."""
    return User.objects.annotate(
        published_count=Count(
            "post", filter=Q(post__status=Post.StatusType.PUBLISHED)
        )
    ).order_by("-published_count", "email")[:TOP_AUTHORS_LIMIT]


def popular_tags(min_posts: int) -> QuerySet[Tag]:
    """Return tags used by at least min_posts posts."""
    return Tag.objects.annotate(
        post_count=Count("post")
    ).filter(post_count__gte=min_posts).order_by("-post_count", "name")


def posts_per_status() -> list[dict[str, Any]]:
    """Return the number of posts grouped by status."""
    return list(Post.objects.values("status")
    .annotate(count=Count("pk"))
    .order_by("status")
    )


def users_activity() -> QuerySet[User]:
    """Return users with correct post and comment counts."""
    return User.objects.annotate(
        post_count=Count("post", distinct=True),
        comment_count=Count("comment", distinct=True),
    )


# Level 8

def search_users_by_full_name(text: str) -> QuerySet[User]:
    """Return users whose full name ("First Last") contains text."""
    return User.objects.annotate(
        full_name = Concat("first_name", Value(" "), "last_name")
    ).filter(full_name__icontains=text)


def published_posts_per_month() -> list[dict[str, Any]]:
    """Return published post counts grouped by month, oldest first."""
    return list(
        Post.objects.filter(status=Post.StatusType.PUBLISHED)
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(count=Count("pk"))
        .order_by("month")
    )


def posts_with_popularity() -> QuerySet[Post]:
    """Return posts with comment count and popularity."""
    return Post.objects.annotate(
        comments_count = Count("comment")
    ).annotate(
        popularity = Case(
            When(comments_count__gte=HOT_COMMENTS_MIN, then=Value(HOT_LABEL)),
            When(comments_count__gte=NORMAL_COMMENTS_MIN, then=Value(NORMAL_LABEL)),
            default=Value(QUIET_LABEL),
            output_field=CharField(),
        )
    )
    


# Level 9

def get_or_create_tag(name: str) -> tuple[Tag, bool]:
    """Return a tag by its unique slug, creating it if missing."""
    return Tag.objects.get_or_create(
        slug=slugify(name), defaults={"name": name}
    )


def publish_old_drafts(days: int) -> int:
    """Publish drafts older than days and update their edit timestamp."""
    now = timezone.now()
    cutoff = now - timedelta(days=days)
    return Post.objects.filter(
        status=Post.StatusType.DRAFT,
        created_at__lt=cutoff,
    ).update(status=Post.StatusType.PUBLISHED, updated_at=now)


def tag_category_posts(category_slug: str, tag_slug: str) -> int:
    """Attach a tag to every post in a category and return its post count."""
    tag = Tag.objects.get(slug=tag_slug)
    posts = Post.objects.filter(category__slug=category_slug)
    post_count = posts.count()
    tag.post_set.add(*posts)
    return post_count


def merge_categories(source_slug: str, target_slug: str) -> int:
    """Move posts to the target category, then delete the source."""
    if source_slug == target_slug:
        raise ValueError("Source and target categories must differ")

    with transaction.atomic():
        source = Category.objects.get(slug=source_slug)
        target = Category.objects.get(slug=target_slug)
        moved_count = Post.objects.filter(category=source).update(category=target)
        source.delete()
    return moved_count


def delete_inactive_users_comments() -> int:
    """Delete comments by inactive users and return the number deleted."""
    deleted_count, _ = Comment.objects.filter(author__is_active=False).delete()
    return deleted_count


# Level 10

def published_feed() -> list[str]:
    """Return n newest published posts as lines"""
    posts = (
        Post.objects.filter(status=Post.StatusType.PUBLISHED)
        .select_related("author", "category")
        .order_by("-created_at", "-pk")[:PUBLISHED_LIMIT]
    )
    return [
        f"{post.title} | {post.author.email} | "
        f"{post.category.name if post.category else UNCATECORIZED_LABEL}"
        for post in posts
    ]



def newest_posts_with_tags() -> list[str]:
    """Return n newest published posts and tags as lines in no more that 2 sql querries."""
    posts = (
        Post.objects.order_by("-created_at", "-pk")
        .prefetch_related("tags")[:NEWEST_POSTS_WITH_TAGS_LIMIT]
        
    )
    return [
        f"{post.title}:  {", ".join(tag.name for tag in post.tags.all())}"
        for post in posts
    ]


def categories_with_published_posts() -> dict[str, list[str]]:
    """Return categories and newest published post titles in at most two queries."""
    categories = Category.objects.prefetch_related(
        Prefetch(
            "post_set",
            queryset=Post.objects.filter(
                status=Post.StatusType.PUBLISHED
            ).order_by("-created_at", "-pk"),
            to_attr="published_posts",
        )
    )
    return {
        category.name: [post.title for post in category.published_posts]
        for category in categories
    }


# Level 11

def posts_with_last_comment() -> QuerySet[Post]:
    """Return published posts with the text of each newest comment."""
    last_comment = (
        Comment.objects.filter(post=OuterRef("pk"))
        .order_by("-created_at", "-pk")
        .values("body")[:1]
    )
    return Post.objects.filter(
        status=Post.StatusType.PUBLISHED
    ).annotate(last_comment=Subquery(last_comment))


def posts_with_staff_comments() -> QuerySet[Post]:
    """Return posts having at least one comment by a staff user."""
    staff_comments = Comment.objects.filter(
        post=OuterRef("pk"), author__is_staff=True
    )
    return Post.objects.filter(Exists(staff_comments))


def users_with_draft_as_latest_post() -> QuerySet[User]:
    """Return users whose newest post is a draft."""
    latest_status = (
        Post.objects.filter(author=OuterRef("pk"))
        .order_by("-created_at", "-pk")
        .values("status")[:1]

    )
    return User.objects.annotate(
        latest_post_status=Subquery(latest_status)
    ).filter(latest_post_status=Post.StatusType.DRAFT)


QUERIES = {
    # Level 1
    1: categories_by_name,
    2: published_posts,
    3: newest_published_posts,
    4: post_by_slug,
    5: active_users_count,
    6: has_drafts,
    7: published_posts_page,

    # Level 2
    8: posts_with_word_in_title,
    9: users_with_email_domain,
    10: posts_without_category,
    11: categories_by_slugs,
    12: posts_in_month,
    13: posts_last_days,
    14: posts_between,

    # Level 3
    15: author_published_posts,
    16: posts_with_tag,
    17: comments_in_category,
    18: users_with_published_posts,
    19: posts_without_tags,
    20: users_without_comments,
    21: posts_with_both_tags,

    # Level 4
    22: search_posts,
    23: published_posts_missing_info,
    24: edited_posts,
    25: comments_by_post_author,
    26: comments_before_post,

    # Level 5
    27: published_authors_emails,
    28: published_posts_overview,

    # Level 6
    29: posts_stats,
    30: average_comments_per_post,

    # Level 7
    31: categories_with_post_count,
    32: categories_with_published_count,
    33: top_authors,
    34: popular_tags,
    35: posts_per_status,
    36: users_activity,

    # Level 8
    37: search_users_by_full_name,
    38: published_posts_per_month,
    39: posts_with_popularity,
    
    # Level 9
    40: get_or_create_tag,
    41: publish_old_drafts,
    42: tag_category_posts,
    43: merge_categories,
    44: delete_inactive_users_comments,

    # Level 10
    45: published_feed,
    46: newest_posts_with_tags,
    47: categories_with_published_posts,

    # Level 11
    48: posts_with_last_comment,
    49: posts_with_staff_comments,
    50: users_with_draft_as_latest_post,

}