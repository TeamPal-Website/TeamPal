from __future__ import annotations
import ast
import sys
from pathlib import Path

def _strip_docstrings(node: ast.AST) -> None:
    if isinstance(node, ast.Module):
        _drop_leading_docstring(node.body)
        for child in node.body:
            _strip_docstrings(child)
        return
    for child in ast.iter_child_nodes(node):
        _strip_docstrings(child)
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        _drop_leading_docstring(node.body)

def _drop_leading_docstring(body: list[ast.stmt]) -> None:
    while body:
        first = body[0]
        if not isinstance(first, ast.Expr):
            break
        val = first.value
        if isinstance(val, ast.Constant) and isinstance(val.value, str):
            body.pop(0)
            continue
        break

def process_file(path: Path) -> bool:
    text = path.read_text(encoding='utf-8')
    try:
        tree = ast.parse(text)
    except SyntaxError as e:
        print(f'SKIP syntax {path}: {e}', file=sys.stderr)
        return False
    _strip_docstrings(tree)
    try:
        new = ast.unparse(tree)
    except Exception as e:
        print(f'SKIP unparse {path}: {e}', file=sys.stderr)
        return False
    out = new if new.endswith('\n') else new + '\n'
    path.write_text(out, encoding='utf-8')
    return True

def main() -> None:
    root = Path(__file__).resolve().parent.parent
    skip_dir = {'.venv', 'venv', 'node_modules', '__pycache__'}
    for path in sorted(root.rglob('*.py')):
        if any((p in skip_dir for p in path.parts)):
            continue
        if process_file(path):
            print(path.relative_to(root))
if __name__ == '__main__':
    main()
