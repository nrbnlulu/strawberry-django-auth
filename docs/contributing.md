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

## Getting started

If you have a specific contribution in mind, be sure to check the [issues](https://github.com/nrbnlulu/strawberry-django-auth/issues) and [projects](https://github.com/nrbnlulu/strawberry-django-auth/projects) in progress - someone could already be working on something similar and you can help out.

## Project setup

After cloning this repo, ensure dependencies are installed by running:

```bash
hatch shell
hatch run migrate
```

## Running tests

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

For live testing on a django project, you can use the testproject.
 Create a different virtualenv, install the dependencies again and run:

```bash
cd testproject
make install-local v=<CURRENT VERSION IN gqlauth.__init__>
```

## Opening Pull Requests

Please fork the project and open a pull request against the main branch.

This will trigger a series of tests and lint checks.

We advise that you format and run lint locally before doing this to save time:

Check linting and formatting

```bash
hatch fmt --check
```

Apply formatting

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
