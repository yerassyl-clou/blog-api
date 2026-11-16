from datetime import timedelta
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import connection
from django.db.models import Model, QuerySet
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from apps.auths.models import User
from apps.blog.models import Comment, Post
from apps.blog.queries import QUERIES

PREVIEW_ROWS = 5
MUTATING_QUERIES = {40, 41, 42, 43, 44}
SAMPLE_ARGS: dict[int, dict[str, Any]] = {
    7: {"page": 1},
    9: {"domain": "example.com"},
    11: {"slugs": ["python", "django"]},
    13: {"days": 30},
    14: {
        "start": timezone.localdate() - timedelta(days=365),
        "end": timezone.localdate(),
    },
    21: {"first_slug": "backend", "second_slug": "docker"},
    34: {"min_posts": 2},

}


class Command(BaseCommand):
    help = "Run ORM queries and show their SQL results"

    def add_arguments(self, parser: CommandParser) -> None:
        """Add comand line arguments."""

        parser.add_argument(
            "--number", type=int, help="Number of query to run"
        )
        parser.add_argument(
            "--sql", action="store_true", help="Print executed SQL"
        )        

    def handle(self, *args, **options):
        """Execute and display ORM queries."""

        selected_number: int | None = options["number"]
        show_sql: bool = options["sql"]

        if selected_number not in QUERIES and selected_number is not None:
            raise CommandError(f"Querry №{selected_number} does not exist")

        if selected_number is None:
            numbers = [
                number
                for number in QUERIES
                if number not in MUTATING_QUERIES
            ]
        else:
            numbers = [selected_number]

        for number in numbers:
            function = QUERIES[number]
            arguments = SAMPLE_ARGS.get(number, {})

            if number == 4:
                slug = Post.objects.order_by("pk").values_list(
                    "slug", flat = True
                ).first()
                arguments = {"slug": slug or ""}

            if number == 8:
                title = Post.objects.order_by("pk").values_list(
                    "title", flat=True
                ).first()
                arguments = {"word": title.split()[0] if title else ""}

            if number == 12:
                created_at = Post.objects.order_by("pk").values_list(
                    "created_at", flat=True
                ).first()
                example_day = created_at.date() if created_at else timezone.now()
                arguments = {"year": example_day.year, "month": example_day.month}

            if number == 15:
                email = Post.objects.filter(
                    status=Post.StatusType.PUBLISHED
                ).values_list("author__email", flat=True).first()
                arguments = {"email": email or ""}

            if number == 16:
                tag_slug = Post.objects.filter(
                    tags__isnull=False
                ).values_list("tags__slug", flat=True).first()
                arguments = {"tag_slug": tag_slug or ""}

            if number == 17:
                category_slug = Comment.objects.filter(
                    post__category__isnull=False
                ).values_list("post__category__slug", flat=True).first()
                arguments = {"category_slug": category_slug or ""}

            if number == 22:
                title = Post.objects.order_by("pk").values_list(
                    "title", flat=True
                ).first()
                arguments = {"text": title.split()[0] if title else ""}

            if number == 37:
                first_name, last_name = (
                    User.objects.order_by("pk").values_list(
                    "first_name", "last_name"
                ).first() or ("", "")
                )
                arguments = {"text": f"{first_name} {last_name}"}

            with CaptureQueriesContext(connection) as context:
                result = function(**arguments)
                anotation_names = (
                    tuple(result.query.annotations)
                    if isinstance(result, QuerySet)
                    else ()
                )

                if isinstance(result, QuerySet):
                    result = list(result)

                sql_count = len(context.captured_queries)
                self.stdout.write(f"№{number} {function.__name__} - {sql_count} query(ies)")

                if show_sql:
                    for captured_query in context.captured_queries:
                        self.stdout.write(captured_query["sql"])

                if isinstance(result, list):
                    for item in result[:PREVIEW_ROWS]:
                        if isinstance(item, Model) and anotation_names:
                            anotations = {
                                name: getattr(item, name)
                                for name in anotation_names
                            }
                            self.stdout.write(f" {item} {anotations}")
                        else:
                            self.stdout.write(f" {item}")
                    self.stdout.write(f"({len(result)} rows)")
                else:
                    self.stdout.write(f" {result}")
            
            
        
            #context.captured_queries[0]["sql"] # the SQL text of the first one
