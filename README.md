# Web Application Exercise

A little exercise to build a web application following an agile development process. See the [instructions](instructions.md) for more detail.

## Product vision statement

A web application that keeps track of a user’s past expenses, allowing users to add, edit, delete, and search for expenses, as well as view statistics about their biggest expenses.

## User stories 

[User Stories](https://github.com/software-students-fall2024/2-web-app-now-you-re-unemployed/issues)

## Steps necessary to run the software

1. Create a `.env` file following this format:
```
MONGO_URI=mongodb://your_db_username:your_db_password@your_db_host_server_name:27017
SECRET_KEY=your_secret_key
```
You will have to create your own database and secret key if not provided one by the team.

2. Install dependencies by using `pipenv`:
```
pipenv shell
```
Or use `pip`:
```
pip3 install -r requirements.txt
```

3. Define this environment variable from the command line:
    1. On Mac: `export FLASK_APP=app.py`
    2. On Windows: `use set FLASK_APP=app.py`

Then start `flask`:
```
flask run
```
Follow the link given.

## Task boards

[Task Board - Sprint 1](https://github.com/orgs/software-students-fall2024/projects/42)

[Task Board - Sprint 2](https://github.com/orgs/software-students-fall2024/projects/76)