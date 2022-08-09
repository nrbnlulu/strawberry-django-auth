<!-- shameless copy from graphene-django CONTRIBUTING file -->

# Contributing

Thanks for helping improve Django GraphQL Auth!

All kinds of contributions are welcome:

- Bug fixes
- Documentation improvements
- New features
- Refactoring
- Fix some typo
- Write more tests

## Getting started

If you have a specific contribution in mind, be sure to check the [issues](https://github.com/nrbnlulu/strawberry-django-auth/issues) and [projects](https://github.com/nrbnlulu/strawberry-django-auth/projects) in progress - someone could already be working on something similar and you can help out.

## Project setup

1. Fork this repository.
2. Clone your fork.
3. Install with poetry - `poetry install`.
4. run `pre-commit install`, this will perform some checks when you commit.
5. create a new branch from the main with the name of your contribution topic.
6. You are good to go!

## Running tests
```bash
make test
```
this will run tests against two django settings modules.


```bash
# python=3.7 and django=3.0
make test
```
tests against other Python version will run on github workflows.

## Documentation

The documentation is generated using the excellent [MkDocs](https://www.mkdocs.org/) with [material theme](https://squidfunk.github.io/mkdocs-material/).

To see that your docs are written well check them with the development server:
```bash
make serve
```

_It will run the `docs/pre_build.py` script before building the docs._
