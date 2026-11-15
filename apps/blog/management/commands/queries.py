from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db.models import Model, QuerySet
from django.test.utils import CaptureQueriesContext
from django.db import connection

from apps.blog.queries import QUERIES


PREVIEW_ROWS = 5
MUTATING_QUERIES = {40, 41, 42, 43, 44}
SAMPLE_ARGS: dict[int, dict[str, Any]] = {}


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
                    self.stdout.write(f" {item}")
            
            
        
            #context.captured_queries[0]["sql"] # the SQL text of the first one
