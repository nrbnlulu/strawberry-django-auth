"""
- get class names and docstrings as context variables into the docs
- copy [CONTRIBUTORS, CHANGES, CONTRIBUTING] files to the docs dir
"""

import shutil
from pathlib import Path

from pydoc_markdown import FilterProcessor
from pydoc_markdown.contrib.loaders.python import PythonLoader
from pydoc_markdown.contrib.renderers.markdown import MarkdownRenderer
from pydoc_markdown.interfaces import Context

if __name__ == "__main__":
    # copy resolvers file from .py to .yml
    root_dir = Path(__file__).parent.parent
    src = root_dir / "gqlauth"
    assert src.exists()
    user_path = src / "user"
    assert user_path.exists()
    docs_path = root_dir / "docs"
    assert docs_path.exists()

    # copy files from project root to docs dir
    files = ["CONTRIBUTORS.md", "RELEASE.md", "CONTRIBUTING.md"]
    dest = ["contributors.md", "changelog.md", "contributing.md"]
    for index, file in enumerate(files):
        shutil.copyfile(root_dir / file, root_dir / "docs" / dest[index])

    context = Context(directory=str(user_path))
    loader = PythonLoader(
        search_path=[str(user_path)],
        modules=[
            "resolvers",
        ],
    )
    renderer = MarkdownRenderer(
        render_module_header=False,
        insert_header_anchors=False,
        descriptive_class_title=False,
        add_module_prefix=False,
        docstrings_as_blockquote=True,
        use_fixed_header_levels=False,
    )

    loader.init(context)
    renderer.init(context)
    modules = list(loader.load())
    processor = FilterProcessor()
    processor.process(modules, None)

    with open(docs_path / "api.md", "w") as f:
        f.write(
            """
> auto generated using `pydoc_markdown`
___
{}
""".format(
                renderer.render_to_string(modules)
            )
        )

    # ------------------------------- Settings -----------------------------------
    context = Context(directory=str(src))
    loader = PythonLoader(
        search_path=[str(src)],
        modules=[
            "settings_type",
        ],
    )
    renderer = MarkdownRenderer(
        render_module_header=False,
        insert_header_anchors=False,
        descriptive_class_title=False,
        add_module_prefix=False,
        docstrings_as_blockquote=True,
        use_fixed_header_levels=False,
        signature_code_block=True,
    )

    loader.init(context)
    renderer.init(context)
    modules = list(loader.load())
    processor = FilterProcessor()
    processor.process(modules, None)

    with open(docs_path / "settings.md", "w") as f:
        f.write(
            """
> auto generated using `pydoc_markdown`
___
{}
""".format(
                renderer.render_to_string(modules)
            )
        )
