import typing
from base64 import b64decode, b64encode

import strawberry
from PIL.Image import Image

image = strawberry.scalar(
    typing.NewType("image", Image),
    serialize=lambda v: b64encode(v).decode("ascii"),
    parse_value=lambda v: b64decode(v),
)
