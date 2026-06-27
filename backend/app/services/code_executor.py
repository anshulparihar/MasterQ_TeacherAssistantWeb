"""
Sandboxed Code Executor for Diagram Generation.

Provides safe execution of LLM-generated Python code that creates matplotlib
or schemdraw diagrams. Code is validated via AST analysis before execution
to block dangerous operations (file I/O, network, subprocess, etc.).

Execution runs in a separate thread with a configurable timeout. The rendered
matplotlib figure is captured as PNG bytes and returned.
"""

import ast
import io
import traceback
import threading
from typing import Tuple

__all__ = [
    "validate_code",
    "execute_diagram_code",
    "CodeValidationError",
    "CodeExecutionTimeout",
    "CodeExecutionError",
]

# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------

class CodeValidationError(Exception):
    """Raised when LLM-generated code fails the AST safety check."""
    pass


class CodeExecutionTimeout(Exception):
    """Raised when code execution exceeds the allowed timeout."""
    pass


class CodeExecutionError(Exception):
    """Raised when a runtime error occurs during code execution."""
    pass


# ---------------------------------------------------------------------------
# Safety Constants
# ---------------------------------------------------------------------------

ALLOWED_MODULES = frozenset({
    "matplotlib",
    "matplotlib.pyplot",
    "matplotlib.patches",
    "matplotlib.lines",
    "matplotlib.text",
    "matplotlib.collections",
    "matplotlib.figure",
    "matplotlib.backends",
    "matplotlib.backends.backend_agg",
    "numpy",
    "math",
    "schemdraw",
    "schemdraw.elements",
})

BLOCKED_MODULES = frozenset({
    "os",
    "sys",
    "subprocess",
    "socket",
    "shutil",
    "pathlib",
    "importlib",
    "ctypes",
    "pickle",
    "shelve",
    "signal",
    "multiprocessing",
    "threading",
    "http",
    "urllib",
    "requests",
    "webbrowser",
    "code",
    "codeop",
    "compileall",
    "py_compile",
    "pty",
    "resource",
    "tempfile",
    "glob",
    "fnmatch",
    "io",
    "builtins",
    "__builtin__",
})

BLOCKED_FUNCTIONS = frozenset({
    "__import__",
    "eval",
    "exec",
    "compile",
    "globals",
    "locals",
    "getattr",
    "setattr",
    "delattr",
    "open",
    "input",
    "breakpoint",
    "exit",
    "quit",
    "memoryview",
    "type",
})

BLOCKED_ATTRIBUTES = frozenset({
    "__builtins__",
    "__class__",
    "__subclasses__",
    "__bases__",
    "__mro__",
    "__globals__",
    "__code__",
    "__import__",
    "__loader__",
    "__spec__",
    "__dict__",
    "__init_subclass__",
    "__reduce__",
    "__reduce_ex__",
})


# ---------------------------------------------------------------------------
# AST Validation
# ---------------------------------------------------------------------------

def _is_allowed_module(module_name: str) -> bool:
    """Check if a module (or any of its parent packages) is in the allow-list."""
    if module_name in BLOCKED_MODULES:
        return False
    # Allow exact matches
    if module_name in ALLOWED_MODULES:
        return True
    # Allow sub-modules of allowed top-level packages
    for allowed in ALLOWED_MODULES:
        if module_name.startswith(allowed + "."):
            return True
    return False


def validate_code(code: str) -> Tuple[bool, str]:
    """
    Parse and validate code for safety using AST analysis.

    Returns:
        (True, '')        – code is safe to execute
        (False, reason)   – code contains a disallowed construct
    """
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return False, f"Syntax error: {exc}"

    for node in ast.walk(tree):
        # --- Import statements ---
        if isinstance(node, ast.Import):
            for alias in node.names:
                if not _is_allowed_module(alias.name):
                    return False, f"Import of '{alias.name}' is not allowed"

        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if not _is_allowed_module(module):
                return False, f"Import from '{module}' is not allowed"

        # --- Blocked function calls ---
        elif isinstance(node, ast.Call):
            func = node.func
            # Direct call: eval(...), exec(...), etc.
            if isinstance(func, ast.Name) and func.id in BLOCKED_FUNCTIONS:
                return False, f"Call to '{func.id}()' is not allowed"
            # Attribute call: os.system(...), etc.
            if isinstance(func, ast.Attribute) and func.attr in BLOCKED_FUNCTIONS:
                return False, f"Call to '.{func.attr}()' is not allowed"

        # --- Blocked attribute access ---
        elif isinstance(node, ast.Attribute):
            if node.attr in BLOCKED_ATTRIBUTES:
                return False, f"Access to '{node.attr}' is not allowed"

        # --- Blocked string references to dangerous names (f-strings, etc.) ---
        elif isinstance(node, ast.Name):
            if node.id in BLOCKED_MODULES and not isinstance(
                getattr(node, "ctx", None), ast.Store
            ):
                # Referencing a blocked module by bare name
                if node.id in ("os", "sys", "subprocess", "socket", "shutil"):
                    return False, f"Reference to '{node.id}' is not allowed"

    return True, ""


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------

def _safe_import(name, globals=None, locals=None, fromlist=(), level=0):
    if not _is_allowed_module(name):
        raise ImportError(f"Import of '{name}' is not allowed")
    return __import__(name, globals, locals, fromlist, level)


def _build_namespace() -> dict:
    """Build the restricted namespace for code execution."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.patches as patches
    import matplotlib.lines as mlines
    import matplotlib.text as mtext
    import matplotlib.collections as mcollections
    import matplotlib.figure
    import matplotlib.backends.backend_agg
    import numpy as np
    import math as _math

    namespace: dict = {
        "plt": plt,
        "matplotlib": matplotlib,
        "patches": patches,
        "mlines": mlines,
        "mtext": mtext,
        "mcollections": mcollections,
        "np": np,
        "math": _math,
        "Figure": matplotlib.figure.Figure,
        "FigureCanvasAgg": matplotlib.backends.backend_agg.FigureCanvasAgg,
        "io": io,  # needed for BytesIO in generated code
        "__builtins__": {
            # Provide only safe builtins
            "__import__": _safe_import,
            "range": range,
            "len": len,
            "int": int,
            "float": float,
            "str": str,
            "bool": bool,
            "list": list,
            "dict": dict,
            "tuple": tuple,
            "set": set,
            "frozenset": frozenset,
            "enumerate": enumerate,
            "zip": zip,
            "map": map,
            "filter": filter,
            "sorted": sorted,
            "reversed": reversed,
            "min": min,
            "max": max,
            "sum": sum,
            "abs": abs,
            "round": round,
            "pow": pow,
            "divmod": divmod,
            "isinstance": isinstance,
            "issubclass": issubclass,
            "hasattr": hasattr,
            "id": id,
            "repr": repr,
            "print": print,  # harmless, captured by Agg backend
            "True": True,
            "False": False,
            "None": None,
            "ValueError": ValueError,
            "TypeError": TypeError,
            "KeyError": KeyError,
            "IndexError": IndexError,
            "RuntimeError": RuntimeError,
            "StopIteration": StopIteration,
            "Exception": Exception,
            "super": super,
            "property": property,
            "staticmethod": staticmethod,
            "classmethod": classmethod,
            "object": object,
            "slice": slice,
            "complex": complex,
            "bytes": bytes,
            "bytearray": bytearray,
            "hex": hex,
            "oct": oct,
            "bin": bin,
            "ord": ord,
            "chr": chr,
            "all": all,
            "any": any,
            "callable": callable,
            "format": format,
            "iter": iter,
            "next": next,
        },
    }

    # Optionally add schemdraw if installed
    try:
        import schemdraw
        import schemdraw.elements as elm
        namespace["schemdraw"] = schemdraw
        namespace["elm"] = elm
    except ImportError:
        pass

    return namespace


def _capture_figure(namespace: dict) -> bytes:
    """
    Capture the matplotlib figure from the execution namespace as PNG bytes.

    Looks for a 'fig' variable first; falls back to plt.gcf().
    """
    import matplotlib.pyplot as plt

    fig = namespace.get("fig", None)
    if fig is None:
        fig = plt.gcf()

    # If the figure is empty, raise so the caller gets a clear error
    if not fig.get_axes() and not fig.texts:
        raise CodeExecutionError(
            "Code executed but produced no visible figure. "
            "Make sure your code creates a plot or assigns a Figure to 'fig'."
        )

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def execute_diagram_code(code: str, timeout: int = 10) -> bytes:
    """
    Safely execute LLM-generated Python code that produces a matplotlib figure.

    1. Validates the code with AST analysis.
    2. Executes in a restricted namespace inside a daemon thread.
    3. Captures the rendered figure as PNG bytes.

    Args:
        code:    Python source code that creates a matplotlib figure.
        timeout: Maximum execution time in seconds (default 10).

    Returns:
        PNG image bytes of the rendered figure.

    Raises:
        CodeValidationError:  if the code fails AST safety checks.
        CodeExecutionTimeout: if execution exceeds the timeout.
        CodeExecutionError:   if a runtime error occurs.
    """
    # --- Step 1: Validate ---
    is_safe, reason = validate_code(code)
    if not is_safe:
        raise CodeValidationError(f"Code validation failed: {reason}")

    # --- Step 2: Execute in thread with timeout ---
    result_container: dict = {}  # mutable container shared with thread

    def _run() -> None:
        try:
            namespace = _build_namespace()
            exec(code, namespace)  # noqa: S102 – code is AST-validated
            png_bytes = _capture_figure(namespace)
            result_container["result"] = png_bytes
        except (CodeExecutionError, CodeValidationError):
            # Re-raise our own exceptions
            result_container["error"] = traceback.format_exc()
        except Exception:
            result_container["error"] = traceback.format_exc()

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    thread.join(timeout=timeout)

    if thread.is_alive():
        # Thread is still running – timeout exceeded.
        # Daemon thread will be cleaned up when the main thread / process exits.
        raise CodeExecutionTimeout(
            f"Code execution timed out after {timeout} seconds"
        )

    if "error" in result_container:
        raise CodeExecutionError(
            f"Runtime error during code execution:\n{result_container['error']}"
        )

    if "result" not in result_container:
        raise CodeExecutionError(
            "Code execution finished but produced no result."
        )

    return result_container["result"]
