from django.db.models import QuerySet

from apps.blog.models import Category

def categories_by_name() -> QuerySet[Category]:
    """All categories, sorted by name"""
    
    return Category.objects.order_by("name")


QUERIES = {
    1: categories_by_name, 
    #2: published_posts, 
}


