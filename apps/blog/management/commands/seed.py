import time
from random import Random
from typing import Any

from django.contrib.auth.hashers import make_password
from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction
from django.utils.text import slugify
from faker import Faker

from apps.auths.models import User
from apps.blog.models import Category, Comment, Post, Tag

FIRST_SUFFIX = 2

DEFAULT_USERS = 20
DEFAULT_POSTS = 100
DEFAULT_COMMENTS = 500

SEED_PASSWORD = "Djangorlar"

INACTIVE_SHARE = 0.1
STAFF_SHARE = 0.1

EMAIL_DOMAIN = "@example.com"

BATCH_SIZE = 200

PUBLISHED_SHARE = 0.7
POST_TITLE_WORDS = 5
UNCATEGORIZED_SHARE = 0.1
POST_PARAGRAPHS = 3

CATEGORY_NAMES = (
    "Python",
    "Django",
    "DevOps",
    "JavaScript",
    "Web Development",
    "Data Science",
    "Machine Learning",
    "Databases",
    "Cybersecurity",
    "Cloud Computing",
)

TAG_NAMES = (
    "Backend",
    "Frontend",
    "Full Stack",
    "REST API",
    "FastAPI",
    "Flask",
    "PostgreSQL",
    "MySQL",
    "MongoDB",
    "Docker",
    "Kubernetes",
    "CI/CD",
    "Git",
    "GitHub",
    "Linux",
    "AWS",
    "Machine Learning",
    "Data Analysis",
    "Automation",
    "Software Architecture",
)

MIN_COMMENT_SENTENCES = 1

MAX_COMMENT_SENTENCES = 3


def unique_value(base: str, used_slugs: set[str]) -> str:
    candidate = base
    suffix_number = FIRST_SUFFIX

    while candidate in used_slugs:
        candidate = f"{base}-{suffix_number}"
        suffix_number += 1

    used_slugs.add(candidate)

    return candidate


class Command(BaseCommand):

    help = "Fill the database with fake data."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument("--users", type=int, default=DEFAULT_USERS, help="Number of users to create")
        parser.add_argument("--posts", type=int, default=DEFAULT_POSTS, help="Number of posts to create")
        parser.add_argument("--comments", type=int, default=DEFAULT_COMMENTS, help="Number of comments to create")
        parser.add_argument("--clear", action="store_true", help="Delete existing data before seeding")
        



    def handle(self, *args: Any, **options: Any) -> None:
        """Command entry point."""
        start_time = time.perf_counter()

        users_count: int = options["users"]
        posts_count: int = options["posts"]
        comments_count: int = options["comments"]
        clear: bool = options["clear"]

        for name, count in (
            ("users", users_count),
            ("posts", posts_count),
            ("comments", comments_count)
        ):
            if count < 0:
                raise CommandError(
                    f"--{name} must be zero or greater"
                )

        fake = Faker()
        rnd = Random()

        with transaction.atomic():
            if clear:
                self.__clear_data()

            self.__create_users(fake, rnd, users_count)

            users = User.objects.all()

            if (posts_count or comments_count) and not users:
                raise CommandError(
                    "Posts or comments require users (use 1 or more user in --users)"
                )

            categories_created = self.__create_named(
                Category,
                CATEGORY_NAMES
            )
            tags_created = self.__create_named(
                Tag,
                TAG_NAMES
            )

            self.__create_posts(
                fake, 
                rnd,
                users,
                posts_count
            )

            published_posts = list (
                Post.objects.filter(status=Post.StatusType.PUBLISHED)
            )

            if comments_count and not published_posts:
                raise CommandError(
                    "Comments require posts (use 1 or more posts in --posts)"
                ) 

            self.__create_comments(
                fake,
                rnd,
                users,
                published_posts,
                comments_count
            )

                   

        self.stdout.write(f"Users: {users_count}")
        self.stdout.write(f"Categories: {categories_created}")
        self.stdout.write(f"Tags: {tags_created}")
        self.stdout.write(f"Posts: {posts_count}")
        self.stdout.write(f"Comments: {comments_count}")

        execution_time = time.perf_counter() - start_time

        self.stdout.write(self.style.SUCCESS(f"Done in {execution_time:.2f} seconds"))

        


    def __create_users(
        self, 
        fake: Faker, 
        rnd: Random,
        count: int
    ) -> None:
        """Function for users creation."""
        if count == 0:
            return

        used_emails = set(
            User.objects.values_list("email", flat=True)
        )

        used_local_parts = set()

        for email in used_emails:
                if email.endswith(EMAIL_DOMAIN):
                    local_part = email.split("@")[0]
                    used_local_parts.add(local_part)
        

        hashed_password = make_password(SEED_PASSWORD)

        inactive_count = round(count * INACTIVE_SHARE)
        staff_count = max(1, round(count * STAFF_SHARE))

        active_flags = (
            [False] * inactive_count + [True] * (count - inactive_count)
        )

        staff_flags = (
            [False] * (count - staff_count) + [True] * staff_count  
        )

        rnd.shuffle(active_flags)
        rnd.shuffle(staff_flags)

        users_to_create: list[User] = []

        for i in range(count):
            first_name = fake.first_name()
            last_name = fake.last_name()

            base = slugify(
                f"{first_name}.{last_name}"
            ).replace("-", ".")

            local_part = unique_value(
                base, used_local_parts,
            )

            users_to_create.append(
                User(
                    email=f"{local_part}{EMAIL_DOMAIN}",
                    first_name=first_name,
                    last_name=last_name,
                    password=hashed_password,
                    is_active=active_flags[i],
                    is_staff=staff_flags[i],
                )
            )

        User.objects.bulk_create(users_to_create, ignore_conflicts=True, batch_size=BATCH_SIZE)

    def __create_named(
        self, 
        model: type[Category] | type[Tag], 
        names: tuple[str]
    ) -> int:
        """Function for posts and categories creation."""
        used_names = set(model.objects.values_list("name", flat=True))
        used_slugs = set(model.objects.values_list("slug", flat=True))

        objects_to_create = []

        for name in names:
            slug = slugify(name)

            if name in used_names or slug in used_slugs:
                continue

            objects_to_create.append(model(name=name, slug=slug))

            used_names.add(name),
            used_slugs.add(slug)

        model.objects.bulk_create(objects_to_create, ignore_conflicts=True, batch_size=BATCH_SIZE)

        return len(objects_to_create)

    def __create_posts(
        self, 
        fake: Faker,
        rnd: Random, 
        users: list[User],
        count:int    
    ) -> None:
        """Function for posts creation."""
        categories = list(Category.objects.all())
        tags = list(Tag.objects.all())

        used_slugs = set(Post.objects.values_list("slug", flat=True))

        published_count = round(count * PUBLISHED_SHARE)

        statuses = (
            [Post.StatusType.PUBLISHED] * published_count + [Post.StatusType.DRAFT] * (count - published_count)  
        )   

        rnd.shuffle(statuses)

        posts_to_create: list[Post] = []

        for status in statuses:
            title = fake.sentence(nb_words=POST_TITLE_WORDS)
            
            if rnd.random() > UNCATEGORIZED_SHARE:
                category = rnd.choice(categories)
            else:
                category = None

            posts_to_create.append(
                Post(
                    author=rnd.choice(users),
                    title=title,
                    slug=unique_value(
                        slugify(title),
                        used_slugs, 
                    ),
                    body="\n\n".join(
                        fake.paragraphs(nb=POST_PARAGRAPHS)
                    ),
                    category=category,
                    status=status,
                )
            )

        Post.objects.bulk_create(posts_to_create, batch_size=BATCH_SIZE)

        created_posts = Post.objects.filter(
            slug__in=[post.slug for post in posts_to_create]
        )

        for post in created_posts:
            tag_count = rnd.randint(0, min(5, len(tags)))
            selected_tags = rnd.sample(tags, tag_count)

            post.tags.set(selected_tags)

    def __create_comments(
        self, 
        fake: Faker,
        rnd: Random, 
        users: list[User],
        published_posts: list[Post],
        count: int
    ) -> None:
        """Function for comments creation."""
        comments_to_create: list[Comment] = []

        for _ in range(count):
            comments_to_create.append(
                Comment(
                    post=rnd.choice(published_posts),
                    author=rnd.choice(users),
                    body=" ".join(
                        fake.sentences(
                            nb=rnd.randint(MIN_COMMENT_SENTENCES, MAX_COMMENT_SENTENCES)
                        )
                    ),
                )
            )

        Comment.objects.bulk_create(comments_to_create, ignore_conflicts=True, batch_size=BATCH_SIZE)

    def __clear_data(self) -> None:
        """Function for data cleaning before adding new."""
        self.stdout.write(self.style.WARNING("clearing existing data"))

        Comment.objects.all().delete()
        Post.objects.all().delete()
        Tag.objects.all().delete()
        Category.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()

        self.stdout.write(self.style.SUCCESS("data cleaned succesfully"))