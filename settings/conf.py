from decouple import config

SECRET_KEY = config('BLOG-SECRET_KEY', cast=str)

ENV_ID = config("BLOG_ENV_ID", cast=str)