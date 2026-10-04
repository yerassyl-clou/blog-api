from django.db import models

from django.db.models import (
    BooleanField,
    CharField,
    EmailField,
    SlugField,
    ForeignKey,
    Model,
    TextChoices,
    DateTimeField,
    CASCADE,
    SET_NULL

)

from apps.auths.models import User


class Category(Model):
    """"Category database table."""

    NAME_MAX_LENGTH = 100

    name = models.CharField(
        max_length=NAME_MAX_LENGTH,
        unique=True
    )
    slug = models.SlugField(
        unique=True
    )


class Tag(Model):
    """"Tag database table."""

    NAME_MAX_LENGTH = 50

    name = models.CharField(
        max_length=NAME_MAX_LENGTH,
        unique=True
    )
    slug = models.SlugField(
        unique=True
    )


class Post(Model):
    """Post database table."""

    TITLE_MAX_LENGTH = 50

    author = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE
    )
    title = models.CharField(
        max_length=TITLE_MAX_LENGTH
    )
    slug = models.SlugField(
        unique=True
    )
    body = models.TextField(
    )
    category = models.ForeignKey(
        to=Category,
        on_delete=models.SET_NULL,
        null=True
    )
    tags = models.ManyToManyField(
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
    post = models.ForeignKey(
        to=Post,
        on_delete=CASCADE
    )
    author = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE
    )
    body = models.TextField(
    )
    created_at = DateTimeField(
        auto_now_add=True
    )