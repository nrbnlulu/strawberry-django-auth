#!/usr/bin/env python
import re
from collections import OrderedDict

from setuptools import find_packages, setup
from pathlib import Path

cwd = Path(__file__).parent
src = Path.cwd() / 'gqlauth'

def get_version():
    init = src / "__init__.py"
    assert init.resolve().exists()
    with open(init) as f:
        pattern = r'^__version__ = [\'"]([^\'"]*)[\'"]'
        return re.search(pattern, f.read(), re.MULTILINE).group(1)


tests_require = [
    "pytest>=3.6.3",
    "pytest-cov>=2.4.0",
    "pytest-django>=4.5.2",
    "coveralls",
    "tox"
]

dev_requires = ["black>=22.3", "flake8>=4.0.1", "tox>=3.25.0 "] + tests_require

setup(
    name="strawberry-django-auth",
    version=get_version(),
    license="MIT",
    description="Graphql authentication system with Strawberry for Django.",
    long_description=open(cwd / "README.rst").read(),
    long_description_content_type="text/x-rst",
    author="nir-benlulu",
    author_email="nrbnlulu@gmail.com",
    maintainer="nir benlulu",
    url="https://github.com/nrbnlulu/strawberry-django-auth",
    project_urls=OrderedDict(
        (
            (
                "Documentation",
                "https://nrbnlulu.github.io/strawberry-django-auth/",
            ),
            ("Issues", "https://github.com/nrbnlulu/strawberry-django-auth/issues"),
        )
    ),
    packages=find_packages(exclude=["tests*"]),
    install_requires=[
        "Django>=4.0",
        "strawberry-django-jwt>=0.2.0",
        "strawberry-graphql-django>=0.2.5",
        "strawberry-graphql>=0.104.3",
        "PyJWT>=2.3.0",
        "Faker>=13.3.4",
        "Pillow>=9.1.0",
    ],
    tests_require=tests_require,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.10",
        "Framework :: Django",
        "Framework :: Django :: 4.0",
    ],
    keywords="api graphql rest relay strawberry auth",
    zip_safe=False,
    include_package_data=True,
    extras_require={"test": tests_require, "dev": dev_requires},
)
