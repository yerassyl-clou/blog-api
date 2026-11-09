from io import StringIO

from django.core.management import CommandError, call_command
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.auths.models import User
from apps.blog.management.commands.seed import SEED_PASSWORD
from apps.blog.models import Category, Comment, Post, Tag

TEST_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


@override_settings(PASSWORD_HASHERS=TEST_HASHERS)
class BlogAdminTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.editor = User.objects.create_superuser(
            "editor@example.com", "Demo", "Editor", "test-password"
        )
        cls.author = User.objects.create_user(
            "author@example.com", "Blog", "Author", "test-password"
        )
        cls.category = Category.objects.create(name="Python", slug="python")
        cls.tag = Tag.objects.create(name="Django", slug="django")
        cls.published = Post.objects.create(
            title="Published article",
            slug="published-article",
            body="Sample body",
            status=Post.StatusType.PUBLISHED,
            author=cls.author,
            category=cls.category,
        )
        cls.published.tags.add(cls.tag)
        cls.draft = Post.objects.create(
            title="Draft article",
            slug="draft-article",
            body="Sample draft",
            status=Post.StatusType.DRAFT,
            author=cls.editor,
        )

    def setUp(self):
        self.client.force_login(self.editor)

    def test_post_list_filters_and_tabs(self):
        url = reverse("admin:blog_post_changelist")
        response = self.client.get(url)
        self.assertContains(response, "Apply Filters")
        self.assertContains(response, "Drafts")
        self.assertEqual(len(response.context["cl"].filter_specs), 5)

        response = self.client.get(
            url,
            {
                "status__exact": Post.StatusType.PUBLISHED,
                "category__id__exact": self.category.pk,
                "tags__id__exact": [self.tag.pk],
                "author__id__exact": self.author.pk,
                "created_at_from_0": "2000-01-01",
            },
        )
        self.assertQuerySetEqual(response.context["cl"].result_list, [self.published])

    def test_comment_author_autocomplete(self):
        response = self.client.get(
            reverse("admin:autocomplete"),
            {
                "app_label": "blog",
                "model_name": "comment",
                "field_name": "author",
                "term": "author@example.com",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"][0]["id"], str(self.author.pk))

    def test_row_publish_requires_post(self):
        url = reverse("admin:blog_post_publish_post", args=[self.draft.pk])
        self.assertContains(self.client.get(url), "Publish this post?")
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.status, Post.StatusType.DRAFT)

        response = self.client.post(
            url, {"_form_submitted": "true"}, HTTP_HX_REQUEST="true"
        )
        self.assertEqual(
            response.headers["HX-Redirect"], reverse("admin:blog_post_changelist")
        )
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.status, Post.StatusType.PUBLISHED)

    def test_save_and_publish_without_a_category(self):
        url = reverse("admin:blog_post_change", args=[self.draft.pk])
        response = self.client.post(
            url,
            {
                "title": self.draft.title,
                "slug": self.draft.slug,
                "body": "Edited draft",
                "status": Post.StatusType.DRAFT,
                "author": self.editor.pk,
                "comment_set-TOTAL_FORMS": 0,
                "comment_set-INITIAL_FORMS": 0,
                "blog_post_save_and_publish": "1",
            },
        )
        self.assertRedirects(response, reverse("admin:blog_post_changelist"))
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.status, Post.StatusType.PUBLISHED)
        self.assertEqual(self.draft.body, "Edited draft")


@override_settings(PASSWORD_HASHERS=TEST_HASHERS)
class SeedTests(TestCase):
    def seed(self, **options):
        output = StringIO()
        call_command("seed", stdout=output, **options)
        return output.getvalue()

    def test_reseed_and_clear(self):
        superuser = User.objects.create_superuser(
            "editor@example.com", "Demo", "Editor", "test-password"
        )
        options = {"users": 2, "posts": 3, "comments": 5}
        self.seed(**options)
        self.seed(**options)
        self.assertEqual(User.objects.count(), 5)
        self.assertEqual(Post.objects.count(), 6)
        self.assertEqual(Comment.objects.count(), 10)
        self.assertTrue(
            User.objects.filter(is_superuser=False)
            .first()
            .check_password(SEED_PASSWORD)
        )
        self.assertFalse(
            Comment.objects.exclude(post__status=Post.StatusType.PUBLISHED).exists()
        )

        self.seed(clear=True, **options)
        self.assertTrue(User.objects.filter(pk=superuser.pk).exists())
        self.assertEqual(User.objects.count(), 3)
        self.assertEqual(Post.objects.count(), 3)
        self.assertEqual(Comment.objects.count(), 5)

    def test_failed_seed_rolls_back(self):
        with self.assertRaisesMessage(CommandError, "at least one published post"):
            self.seed(users=1, posts=0, comments=1)
        self.assertFalse(User.objects.exists())
