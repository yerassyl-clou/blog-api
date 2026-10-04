from decouple import config

from settings.base import * #noqa

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ["*"]



# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('BLOG_POSTGRES_DB', cast=str),
        "USER": config('BLOG_POSTGRES_USER', cast=str),
        "PASSWORD": config("BLOG_POSTGRES_USER", cast=str),
        "HOST": config("BLOG_POSTGRES_HOST", cast=str),
        "PORT": config("BLOG_POSTGRES_PORT", cast=str),
    }
}
