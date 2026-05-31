"""Генерирует Markdown-документацию из docstring в корневую папку docs/."""

from __future__ import annotations

import ast
import re
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = BACKEND_DIR.parent
DOCS_DIR = ROOT_DIR / 'docs'
SRC_DIR = BACKEND_DIR / 'src'

PACKAGE_SECTIONS: tuple[tuple[str, str, Path], ...] = (
    ('services.md', 'Сервисы', SRC_DIR / 'services'),
    ('repositories.md', 'Репозитории', SRC_DIR / 'repositories'),
    ('errors.md', 'Ошибки', SRC_DIR / 'errors'),
)


def docstring_to_md(text: str | None) -> str:
    if not text or not text.strip():
        return '_Нет описания._\n'

    lines: list[str] = []
    for raw in text.strip().splitlines():
        line = raw.strip()
        if not line:
            lines.append('')
            continue

        if match := re.match(r':param ([^:]+): (.+)', line):
            lines.append(f"- **{match.group(1).strip()}** — {match.group(2).strip()}")
            continue
        if match := re.match(r':type ([^:]+): (.+)', line):
            lines.append(f"  - *тип* `{match.group(2).strip()}`")
            continue
        if match := re.match(r':returns?: (.+)', line):
            lines.append(f"- **Возвращает** — {match.group(1).strip()}")
            continue
        if match := re.match(r':rtype: (.+)', line):
            lines.append(f"  - *тип* `{match.group(1).strip()}`")
            continue
        if match := re.match(r':raises ([^:]+): (.+)', line):
            lines.append(f"- **`{match.group(1).strip()}`** — {match.group(2).strip()}")
            continue
        if match := re.match(r':ivar ([^:]+): (.+)', line):
            lines.append(f"- **{match.group(1).strip()}** — {match.group(2).strip()}")
            continue

        lines.append(line)

    return '\n'.join(lines) + '\n'


def format_args(node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    parts: list[str] = []
    all_args = list(node.args.args)
    defaults = [None] * (len(all_args) - len(node.args.defaults)) + list(node.args.defaults)

    for arg, default in zip(all_args, defaults, strict=False):
        if arg.arg in {'self', 'cls'}:
            continue
        if default is None:
            parts.append(arg.arg)
        elif isinstance(default, ast.Constant):
            value = default.value
            if isinstance(value, str):
                parts.append(f"{arg.arg}='{value}'")
            else:
                parts.append(f'{arg.arg}={value!r}')
        else:
            parts.append(f'{arg.arg}=...')

    if node.args.vararg:
        parts.append(f'*{node.args.vararg.arg}')
    if node.args.kwarg:
        parts.append(f'**{node.args.kwarg.arg}')

    return ', '.join(parts)


def format_callable(name: str, node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    prefix = 'async def' if isinstance(node, ast.AsyncFunctionDef) else 'def'
    return f'`{prefix} {name}({format_args(node)})`'


def render_callable(title_prefix: str, name: str, node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    doc = ast.get_docstring(node)
    return f'{title_prefix} {format_callable(name, node)}\n\n{docstring_to_md(doc)}'


def iter_functions(
    body: list[ast.stmt],
) -> list[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef]]:
    items: list[tuple[str, ast.FunctionDef | ast.AsyncFunctionDef]] = []
    for node in body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            items.append((node.name, node))
    return items


def render_class(node: ast.ClassDef) -> str:
    parts = [f'### class `{node.name}`\n', docstring_to_md(ast.get_docstring(node))]

    for name, func in iter_functions(node.body):
        parts.append(render_callable('####', name, func))

    return '\n'.join(parts) + '\n'


def render_module(path: Path) -> str:
    tree = ast.parse(path.read_text(encoding='utf-8'))
    module_name = path.relative_to(BACKEND_DIR).with_suffix('').as_posix().replace('/', '.')
    chunks = [f'## `{module_name}`\n', docstring_to_md(ast.get_docstring(tree))]

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            chunks.append(render_class(node))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            chunks.append(render_callable('###', node.name, node))

    return '\n'.join(chunks) + '\n'


def write_section(filename: str, title: str, package_dir: Path) -> None:
    chunks = [f'# {title}\n']
    for path in sorted(package_dir.glob('*.py')):
        if path.name == '__init__.py':
            continue
        chunks.append(render_module(path))
    (DOCS_DIR / filename).write_text('\n'.join(chunks).rstrip() + '\n', encoding='utf-8')


def write_index() -> None:
    links = '\n'.join(f'- [{title}]({filename})' for filename, title, _ in PACKAGE_SECTIONS)
    content = f"""# Документация TeamPal Backend

Автоматически сгенерировано из docstring модулей `services`, `repositories` и `errors`.

{links}
"""
    (DOCS_DIR / 'index.md').write_text(content, encoding='utf-8')


def main() -> None:
    DOCS_DIR.mkdir(parents=True, exist_ok=True)

    for filename, title, package_dir in PACKAGE_SECTIONS:
        write_section(filename, title, package_dir)
    write_index()

    print(f'Документация записана в {DOCS_DIR}')


if __name__ == '__main__':
    main()
