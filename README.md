# Blog API

Django course project for a blog.

![Database diagram](docs/erd.png)

## Seed Data

`python3 manage.py seed` creates demo data for users, posts, comments, tags, and categories.

### Available options

```bash
--users       Number of users to create.
--posts       Number of posts to create.
--comments    Number of comments to create.
--clear       Clear existing demo data before generating new data.
```

## Admin screenshots

#### Dashboard

![Dashboard](docs/screenshots/dashboard.png)

#### Post edit page

![Post_edit_page](docs/screenshots/post_edit_page.png)

#### Post list with filters open

![Post list with filters open](docs/screenshots/post_list_with_filters_open.png)

#### Users list

![Users list](docs/screenshots/user_list.png)

## Querries

`python3 manage.py querries` runs SQL queries on the Blog API's data.

```bash
--number    Specify the query number to execute.
--sql       Display the actual SQL query.
```
