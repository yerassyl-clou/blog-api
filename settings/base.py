from pathlib import Path

from django.urls import reverse_lazy

from settings.conf import *

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Application definition

DJANGO_AND_THIRD_PARTY = [
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

CUSTOM_APPS = [
    "apps.auths.apps.AuthsConfig",
    "apps.blog.apps.BlogConfig",
]


INSTALLED_APPS = DJANGO_AND_THIRD_PARTY + CUSTOM_APPS

UNFOLD = {
    "SITE_TITLE": "Blog api admin",
    "SITE_HEADER": "Blog api",
    "SITE_SUBHEADER": "Content management",
    "SITE_SYMBOL": "speed",  # symbol from icon set
    "COLORS": {
        "primary": {
            "50": "oklch(84.0% 0.054 206.650)",
            "100": "oklch(83.5% 0.097 195.456)",
            "200": "oklch(82.7% 0.059 204.238)",
            "300": "oklch(81.2% 0.083 201.487)",
            "400": "oklch(80.7% 0.063 207.489)",
            "500": "oklch(78.8% 0.069 206.534)",
            "600": "oklch(77.8% 0.090 195.458)",
            "700": "oklch(72.6% 0.084 195.459)",
            "800": "oklch(67.6% 0.077 195.482)",
            "900": "oklch(63.0% 0.072 195.474)",
            "950": "oklch(48.0% 0.055 195.474)",
        },
    },
    "ENVIRONMENT": "apps.blog.callbacks.environment_callback",
    "DASHBOARD_CALLBACK": "apps.blog.callbacks.dashboard_callback",
    "COMMAND": {
        "search_models": True,
        "show_history": True,  # Enable history
    },
    "SITE_DROPDOWN": [
        {
            "icon": "code",
            "title": "GitHub",
            "link": "https://github.com/yerassyl-clou/blog-api",
        },
        {
            "icon": "diamond",
            "title": "Unfold docs",
            "link": "https://unfoldadmin.com/docs/",
        },
    ],
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": "apps.blog.callbacks.sidebar_navigation",
    },
    "TABS": [
        {
            "models": [
                "blog.post",
            ],
            "items": [
                {
                    "title": "All",
                    "active": lambda request: not request.GET.get("status__exact"),
                    "link": reverse_lazy("admin:blog_post_changelist"),
                },
                {
                    "title": "Published",
                    "link": reverse_lazy(
                        "admin:blog_post_changelist",
                        query={"status__exact": "published"},
                    ),
                },
                {
                    "title": "Drafts",
                    "link": reverse_lazy(
                        "admin:blog_post_changelist", query={"status__exact": "draft"}
                    ),
                },
            ],
        },
    ],
}


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "settings.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

ASGI_APPLICATION = "settings.asgi.application"
WSGI_APPLICATION = "settings.wsgi.application"


# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_USER_MODEL = "auths.User"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
