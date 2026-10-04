from django.db.models import (
    CASCADE,
    SET_NULL,
    CharField,
    DateTimeField,
    ForeignKey,
    ManyToManyField,
    Model,
    SlugField,
    TextChoices,
    TextField,
)

from apps.auths.models import User


class Category(Model):
    """"Category database table."""

    NAME_MAX_LENGTH = 100

    name = CharField(
        max_length=NAME_MAX_LENGTH,
        unique=True
    )
    slug = SlugField(
        unique=True
    )


class Tag(Model):
    """"Tag database table."""

    NAME_MAX_LENGTH = 50

    name = CharField(
        max_length=NAME_MAX_LENGTH,
        unique=True
    )
    slug = SlugField(
        unique=True
    )


class Post(Model):
    """Post database table."""

    TITLE_MAX_LENGTH = 50

    author = ForeignKey(
        to=User,
        on_delete=CASCADE
    )
    title = CharField(
        max_length=TITLE_MAX_LENGTH
    )
    slug = SlugField(
        unique=True
    )
    body = TextField(
    )
    category = ForeignKey(
        to=Category,
        on_delete=SET_NULL,
        null=True
    )
    tags = ManyToManyField(
        to=Tag,
        blank=True
    )
    status = TextChoices(
        "draft",
        "published"
    )
    created_at = DateTimeField(
        auto_now_add=True
    )
    updated_at = DateTimeField(
        auto_now=True
    )


class Comment(Model):
    """"Comment database table."""
    post = ForeignKey(
        to=Post,
        on_delete=CASCADE
    )
    author = ForeignKey(
        to=User,
        on_delete=CASCADE
    )
    body = TextField(
    )
    created_at = DateTimeField(
        auto_now_add=True
    )