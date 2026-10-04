from django.contrib import admin

from apps.blog.models import Category, Comment, Post, Tag


@admin.register(Category)
class CategotyAdmin(admin.ModelAdmin):
    """Category admin configuration class."""
    
@admin.register(Tag)
class TagAdmmin(admin.ModelAdmin):
    """Tag admin configuration class."""
    
@admin.register(Post)
class PostAdmmin(admin.ModelAdmin):
    """Post admin configuration class."""

@admin.register(Comment)
class CommentAdmmin(admin.ModelAdmin):
    """Comment admin configuration class."""
