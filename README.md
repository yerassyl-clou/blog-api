# Blog API

Django course project for a blog.

![Database diagram](docs/erd.png)

## Seed data

´python3 manage.py seed´ creates demo data for users, posts, comments, tags and categories

´´´
--users
--posts
--comments
--clear
´´´

Example of usage
´´´python
python3 manage.py seed --users 30 --posts 100 --comments 500 --clear
´´´

## Admin screenshots

#### Dashboard

![Dashboard](docs/screenshots/dashboard.png)

#### Post edit page

![Post_edit_page](docs/screenshots/post_edit_page.png)

#### Post list with filters open

![Post list with filters open](docs/screenshots/post_list_with_filters_open.png)

#### Users list

![Users list](docs/screenshots/user_list.png)
