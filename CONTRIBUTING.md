<!-- shameless copy from graphene-django CONTRIBUTING file -->

# Contributing

Thanks for helping improve Strawberry Django Auth!

All kinds of contributions are welcome:

- Bug fixes
- Documentation improvements
- New features
- Refactoring
- Fix some typo
- Write more tests

## Getting Started

If you have a specific contribution in mind, be sure to check the [issues](https://github.com/nrbnlulu/strawberry-django-auth/issues) and [projects](https://github.com/nrbnlulu/strawberry-django-auth/projects) in progress - someone could already be working on something similar and you can help out.

## Project Setup

```bash
hatch run bootstrap
```

This will migrate the database and create a super user with the following credentials:
```
phone_number: 1234567890
password: 1234567890
```

## Development

### Run the development server

```bash
hatch run serve
```

### Activate the default environment and run manually

```bash
hatch shell
./manage.py runserver
```


## Running Tests

After developing, you can run tests with:

```bash
hatch run test
```

You can specify versions, for the full list see tool.hatch.envs.test.matrix in the `pyproject.toml`  file.

```bash
# python=3.12 and django=5.0.3
hatch run test.py3.12-5.0.3:test
```

Single file test:

```bash
# run only tests in tests/test_jwt.py
hatch run test tests/test_jwt.py
```

Run tests across all versions in the test matrix:

```bash
hatch run test:test
```

## Opening Pull Requests

Please fork the project and open a pull request against the main branch.

This will trigger a series of tests and lint checks.

We advise that you format and run lint locally before doing this to save time:

### Check linting and formatting

```bash
hatch fmt --check
```

### Apply formatting

```bash
hatch fmt
```

## Documentation

The documentation is generated using the excellent [MkDocs](https://www.mkdocs.org/) with [material theme](https://squidfunk.github.io/mkdocs-material/).

The documentation is built by running:

```bash
hatch run docs:build
```

Then to produce a HTML version of the documentation, for live editing:

```bash
hatch run docs:serve
```

It will run the `docs/pre_build.py` script before building the docs.

## Examples

### Change the directory

```bash
cd examples/quickstart
```

### Setup the example project

```bash
hatch run bootstrap
```

This will migrate the database and create users with the following credentials
```
username: user1, user2, etc.
password: 123456
```

### Run the Server

```bash
hatch run serve
```