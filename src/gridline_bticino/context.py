"""Per-call workspace; no process-wide mutable project and no author paths."""
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path

_root = ContextVar('bticino_workspace')
_out = ContextVar('bticino_output')


def root():
    try:
        return _root.get()
    except LookupError as exc:
        raise RuntimeError('BTicino workspace context required') from exc


def output_root():
    return _out.get()


@contextmanager
def workspace(path, output=None):
    token = _root.set(Path(path).resolve())
    out_token = _out.set(Path(output).resolve() if output else root()/'output')
    try:
        yield root()
    finally:
        _out.reset(out_token)
        _root.reset(token)
