# backend/agents/notebook/kernel.py
"""
Jupyter kernel management for the notebook-based coder agent.

Manages kernel lifecycle and code execution with proper async handling.
Uses asyncio.to_thread() for blocking jupyter_client calls to avoid
event loop contention issues.
"""

import asyncio
import os
import re
import queue
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, AsyncGenerator
from contextlib import asynccontextmanager

from jupyter_client import KernelManager
from jupyter_client.blocking import BlockingKernelClient

from backend.agents.notebook.schema import CellOutput, KernelState, VariableInfo
from backend.agents.session_context import get_logger

logger = get_logger(__name__)

# ANSI escape code pattern for cleaning tracebacks
ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')


class NotebookKernel:
    """
    Manages a Jupyter kernel for notebook execution.

    Each notebook gets its own kernel instance. The kernel maintains
    state (variables, imports) between cell executions.

    Uses synchronous jupyter_client wrapped in asyncio.to_thread()
    to avoid event loop contention issues that plague async clients.
    """

    def __init__(self, notebook_path: str, working_dir: str, kernel_name: str = "python3"):
        """
        Initialize kernel manager.

        Args:
            notebook_path: Path to the notebook (used as key, not for execution)
            working_dir: Directory where the kernel runs (cwd)
            kernel_name: Jupyter kernel spec name.
                - "python3" → CPython 3.12 (default)
                - "ir"      → R 4.2.2 via IRkernel (requires r-base in container)
        """
        self.notebook_path = notebook_path
        self.working_dir = working_dir
        self.kernel_name = kernel_name
        self.km: Optional[KernelManager] = None
        self.kc: Optional[BlockingKernelClient] = None
        self.execution_count = 0
        self.started_at: Optional[datetime] = None
        self.last_activity: Optional[datetime] = None
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        """Start the kernel process."""
        async with self._lock:
            if self.km and self.km.is_alive():
                logger.info(f"Kernel already running for {self.notebook_path}")
                return

            logger.info(f"Starting kernel for {self.notebook_path} in {self.working_dir}")

            def _start_kernel():
                # Ensure working directory exists
                os.makedirs(self.working_dir, exist_ok=True)

                # Create kernel manager using the requested kernel spec
                km = KernelManager(kernel_name=self.kernel_name)

                # Set connection file directory
                connection_dir = os.path.join(self.working_dir, ".jupyter_runtime")
                os.makedirs(connection_dir, exist_ok=True)
                km.connection_dir = connection_dir

                # Start kernel in working directory
                km.start_kernel(cwd=self.working_dir)

                # Create blocking client
                kc = km.blocking_client()
                kc.start_channels()

                # Wait for kernel to be ready
                kc.wait_for_ready(timeout=30)

                return km, kc

            try:
                self.km, self.kc = await asyncio.to_thread(_start_kernel)
                self.started_at = datetime.now()
                self.last_activity = datetime.now()
                self.execution_count = 0

                # Set up per-user environment and kernel-specific defaults
                await self._setup_user_environment()

                logger.info(
                    f"Kernel '{self.kernel_name}' started successfully for {self.notebook_path}"
                )

            except Exception as e:
                logger.error(f"Failed to start kernel: {e}")
                await self.stop()
                raise RuntimeError(f"Kernel start failed: {e}")

    async def _setup_user_environment(self) -> None:
        """
        Configure the per-user package environment and kernel-specific defaults.

        For Python kernels:
          - Adds the user's persistent venv (at working_dir/../.venv) to sys.path
          - Sets PIP_TARGET so !pip install goes to that same venv (per-user,
            persisted on the Docker volume at ./data/workspace/<user_id>/.venv)
          - Configures matplotlib for inline output

        For R kernels:
          - Adds working_dir/../r_libs to .libPaths() so install.packages()
            and library() use the user's persistent R library directory
        """
        if self.kernel_name == "ir":
            await self._setup_r_environment()
        else:
            await self._setup_matplotlib()

    async def _setup_r_environment(self) -> None:
        """Configure R kernel: per-user library path + display options."""
        setup_code = r"""
# ── Per-user persistent R library ───────────────────────────────────────────
# working dir is /workspace_data/{user_id}/{task_id}; user dir is one level up
.mentori_user_dir <- dirname(getwd())
.mentori_r_libs   <- file.path(.mentori_user_dir, "r_libs")
dir.create(.mentori_r_libs, recursive = TRUE, showWarnings = FALSE)
# Prepend to .libPaths() so install.packages() and library() use it first
if (!(.mentori_r_libs %in% .libPaths())) {
    .libPaths(c(.mentori_r_libs, .libPaths()))
}
# Clean up helper vars
rm(.mentori_user_dir, .mentori_r_libs)

# ── Display options ──────────────────────────────────────────────────────────
options(warn = 1)          # Print warnings immediately
options(width = 120)       # Wide output
options(repr.plot.width  = 7, repr.plot.height = 5, repr.plot.res = 120)
# White background so plots render correctly on dark UI themes
options(repr.plot.bg = "white")
# Also set the base graphics device background for par()-based plots
par(bg = "white", fg = "black", col.axis = "black", col.lab = "black")
"""
        async for _ in self.execute(setup_code, timeout=15, silent=True):
            pass
        logger.info(f"R environment configured for {self.notebook_path}")

    async def _setup_matplotlib(self) -> None:
        """Configure Python kernel: per-user venv on sys.path + matplotlib inline."""
        # ── Per-user venv injection ──────────────────────────────────────────
        # working_dir = /workspace_data/{user_id}/{task_id}
        # user_dir    = /workspace_data/{user_id}
        # venv        = /workspace_data/{user_id}/.venv
        venv_injection = f"""
import os as _os, sys as _sys
from pathlib import Path as _Path
_user_dir  = _Path({repr(self.working_dir)}).parent
_venv_pkgs = _user_dir / ".venv" / "lib"
if _venv_pkgs.exists():
    # Find the actual python3.x subdirectory inside lib/
    for _d in _venv_pkgs.iterdir():
        _sp = _d / "site-packages"
        if _sp.exists() and str(_sp) not in _sys.path:
            _sys.path.insert(0, str(_sp))
            break
# Direct !pip install to the user venv so packages persist across sessions
_venv_root = str(_user_dir / ".venv")
if _os.path.exists(_venv_root):
    _os.environ["VIRTUAL_ENV"]  = _venv_root
    _os.environ["PIP_TARGET"]   = ""  # clear any conflicting target
del _os, _sys, _Path, _user_dir, _venv_pkgs, _venv_root
"""
        async for _ in self.execute(venv_injection, timeout=10, silent=True):
            pass

        setup_code = """
import warnings
warnings.filterwarnings('ignore')

# Configure matplotlib for inline output using IPython's display system
try:
    # Use inline backend for automatic figure capture
    import matplotlib
    matplotlib.use('module://matplotlib_inline.backend_inline')
except ImportError:
    try:
        import matplotlib
        matplotlib.use('Agg')
    except ImportError:
        pass

try:
    import matplotlib.pyplot as plt
    from IPython.display import display, HTML
    import io
    import base64

    # Store original show
    _original_show = plt.show

    def _inline_show(*args, **kwargs):
        '''Capture current figure and display as image'''
        import matplotlib.pyplot as plt
        from IPython.display import display

        # Get all figures
        figs = [plt.figure(i) for i in plt.get_fignums()]
        for fig in figs:
            display(fig)

        # Close figures to prevent memory leak
        if kwargs.get('block', True):
            plt.close('all')

    plt.show = _inline_show

    # Also configure rcParams for better output
    plt.rcParams['figure.dpi'] = 100
    plt.rcParams['savefig.dpi'] = 100
    plt.rcParams['figure.facecolor'] = 'white'
    plt.rcParams['axes.facecolor'] = 'white'
    plt.rcParams['savefig.facecolor'] = 'white'
except ImportError:
    pass

# Set pandas display options
try:
    import pandas as pd
    pd.set_option('display.max_rows', 20)
    pd.set_option('display.max_columns', 10)
    pd.set_option('display.width', 120)
except ImportError:
    pass
"""
        # Execute silently
        async for _ in self.execute(setup_code, timeout=10, silent=True):
            pass

    async def stop(self) -> None:
        """Stop the kernel."""
        async with self._lock:
            if self.kc:
                try:
                    self.kc.stop_channels()
                except Exception as e:
                    logger.warning(f"Error stopping channels: {e}")
                self.kc = None

            if self.km:
                try:
                    def _shutdown():
                        self.km.shutdown_kernel(now=True)

                    await asyncio.to_thread(_shutdown)
                except Exception as e:
                    logger.warning(f"Error shutting down kernel: {e}")
                self.km = None

            logger.info(f"Kernel stopped for {self.notebook_path}")

    async def restart(self) -> None:
        """Restart the kernel (clears all state)."""
        logger.info(f"Restarting kernel for {self.notebook_path}")
        await self.stop()
        await self.start()

    def is_alive(self) -> bool:
        """Check if kernel is running."""
        return self.km is not None and self.km.is_alive()

    async def interrupt(self) -> None:
        """Interrupt current execution."""
        if self.km and self.km.is_alive():
            def _interrupt():
                self.km.interrupt_kernel()

            await asyncio.to_thread(_interrupt)
            logger.info(f"Kernel interrupted for {self.notebook_path}")

    async def execute(
        self,
        code: str,
        timeout: int = 60,
        silent: bool = False
    ) -> AsyncGenerator[CellOutput, None]:
        """
        Execute code and yield outputs as they arrive.

        Args:
            code: Python code to execute
            timeout: Maximum execution time in seconds
            silent: If True, don't increment execution count

        Yields:
            CellOutput objects as outputs arrive
        """
        if not self.is_alive():
            raise RuntimeError("Kernel is not running")

        self.last_activity = datetime.now()

        if not silent:
            self.execution_count += 1

        # Queue for inter-thread communication
        q = queue.Queue()
        sentinel = object()

        def _worker():
            """
            Producer thread: executes code and puts outputs into queue.
            """
            try:
                # Submit execution
                msg_id = self.kc.execute(code, silent=silent, store_history=not silent)
                start_time = datetime.now()

                while True:
                    # Check timeout
                    elapsed = (datetime.now() - start_time).total_seconds()
                    if elapsed > timeout:
                        q.put(CellOutput(
                            output_type="error",
                            ename="TimeoutError",
                            evalue=f"Execution timed out after {timeout}s",
                            traceback=[f"TimeoutError: Cell execution exceeded {timeout}s limit"]
                        ))
                        # Try to interrupt
                        self.km.interrupt_kernel()
                        break

                    try:
                        # Get message with short timeout to allow loop to check timeout
                        msg = self.kc.get_iopub_msg(timeout=0.5)
                    except queue.Empty:
                        continue

                    msg_type = msg.get("msg_type", "")
                    content = msg.get("content", {})
                    parent_id = msg.get("parent_header", {}).get("msg_id", "")

                    # Only process messages for our execution
                    if parent_id != msg_id:
                        continue

                    if msg_type == "status":
                        if content.get("execution_state") == "idle":
                            break

                    elif msg_type == "stream":
                        q.put(CellOutput(
                            output_type="stream",
                            stream_name=content.get("name", "stdout"),
                            text=content.get("text", "")
                        ))

                    elif msg_type == "execute_result":
                        q.put(CellOutput(
                            output_type="execute_result",
                            data=content.get("data", {}),
                            execution_count=content.get("execution_count")
                        ))

                    elif msg_type == "display_data":
                        q.put(CellOutput(
                            output_type="display_data",
                            data=content.get("data", {})
                        ))

                    elif msg_type == "error":
                        # Clean ANSI codes from traceback
                        traceback = content.get("traceback", [])
                        clean_traceback = [
                            ANSI_ESCAPE.sub("", line)
                            for line in traceback
                        ]

                        q.put(CellOutput(
                            output_type="error",
                            ename=content.get("ename", "Error"),
                            evalue=content.get("evalue", ""),
                            traceback=clean_traceback
                        ))

            except Exception as e:
                logger.error(f"Worker execution error: {e}")
                q.put(CellOutput(
                    output_type="error",
                    ename=type(e).__name__,
                    evalue=str(e),
                    traceback=[f"SystemError: {e}"]
                ))
            finally:
                q.put(sentinel)

        # Run worker in separate thread
        loop = asyncio.get_running_loop()
        future = loop.run_in_executor(None, _worker)

        # Consumer loop: yield from queue
        while True:
            try:
                # Non-blocking check
                item = q.get_nowait()
                
                if item is sentinel:
                    break
                    
                yield item
                
            except queue.Empty:
                if future.done():
                    # Thread finished but queue is empty (and we haven't seen sentinel?)
                    # This implies _worker finished. Wait one more loop for sentinel.
                    if future.exception():
                        # If thread crashed without finally block (unlikely)
                         logger.error(f"Execution thread failed: {future.exception()}")
                         yield CellOutput(
                             output_type="error",
                             ename="SystemError",
                             evalue="Execution thread failed",
                             traceback=[str(future.exception())]
                         )
                         break
                
                # Yield control to event loop
                await asyncio.sleep(0.05)

    def get_idle_time(self) -> timedelta:
        """Get time since last activity."""
        if self.last_activity is None:
            return timedelta(0)
        return datetime.now() - self.last_activity

    async def get_kernel_variables(self) -> KernelState:
        """
        Get current kernel state including all user-defined variables.

        Executes introspection code in the kernel to extract:
        - Variable names and types
        - Shapes for arrays/DataFrames
        - Column names for DataFrames
        - Value previews for simple types

        Returns:
            KernelState with all variable information
        """
        if not self.is_alive():
            return KernelState(is_alive=False, execution_count=self.execution_count)

        # Introspection code to run in the kernel
        introspection_code = '''
import json as _json

def _mentori_get_var_info(name, obj):
    """Extract information about a variable."""
    info = {
        "name": name,
        "var_type": type(obj).__name__
    }

    # Get shape for array-like objects
    if hasattr(obj, 'shape'):
        info["shape"] = str(obj.shape)
    elif hasattr(obj, '__len__') and not isinstance(obj, (str, dict)):
        try:
            info["length"] = len(obj)
        except:
            pass

    # Get columns for DataFrames
    if hasattr(obj, 'columns'):
        try:
            cols = list(obj.columns)
            info["columns"] = cols[:30]  # Limit to 30 columns
            if len(cols) > 30:
                info["columns_truncated"] = True
        except:
            pass

    # Get dtype for arrays/series
    if hasattr(obj, 'dtype'):
        info["dtype"] = str(obj.dtype)

    # Get value preview for simple types
    if isinstance(obj, (int, float, bool)):
        info["value_preview"] = repr(obj)
    elif isinstance(obj, str):
        if len(obj) <= 100:
            info["value_preview"] = repr(obj)
        else:
            info["value_preview"] = repr(obj[:100] + "...")
    elif isinstance(obj, (list, tuple)) and len(obj) <= 5:
        try:
            info["value_preview"] = repr(obj)[:200]
        except:
            pass
    elif isinstance(obj, dict) and len(obj) <= 5:
        try:
            info["value_preview"] = repr(obj)[:200]
        except:
            pass

    return info

def _mentori_get_kernel_state():
    """Get all user-defined variables in the kernel."""
    # Built-in names to exclude
    _exclude = {
        '_mentori_get_var_info', '_mentori_get_kernel_state', '_json',
        'In', 'Out', 'get_ipython', 'exit', 'quit',
        '_ih', '_oh', '_dh', '__', '___', '__builtin__', '__builtins__',
        '__doc__', '__loader__', '__name__', '__package__', '__spec__',
        '_i', '_ii', '_iii', '_i1', '_i2', '_i3', '_',
        '_1', '_2', '_3', '_4', '_5', '_6', '_7', '_8', '_9',
        '_sh', '_exit_code', '_getattr_', '_getitem_',
        '_original_show', '_inline_show',  # From our matplotlib setup
    }

    # Also exclude private variables and modules
    import types

    variables = []
    g = globals()

    for name in sorted(g.keys()):
        # Skip private/magic names
        if name.startswith('_'):
            continue
        # Skip excluded names
        if name in _exclude:
            continue

        obj = g[name]

        # Skip modules, functions, classes, and types (unless user-created)
        if isinstance(obj, types.ModuleType):
            continue
        if isinstance(obj, (types.FunctionType, types.BuiltinFunctionType)):
            continue
        if isinstance(obj, type):
            continue

        try:
            info = _mentori_get_var_info(name, obj)
            variables.append(info)
        except Exception as e:
            variables.append({
                "name": name,
                "var_type": "unknown",
                "error": str(e)
            })

    return _json.dumps({"variables": variables})

# Execute and print result
print(_mentori_get_kernel_state())
'''

        # Execute introspection code silently
        result_text = ""
        async for output in self.execute(introspection_code, timeout=10, silent=True):
            if output.output_type == "stream" and output.stream_name == "stdout":
                result_text += output.text or ""
            elif output.output_type == "error":
                logger.warning(f"Kernel introspection error: {output.evalue}")
                return KernelState(
                    is_alive=True,
                    execution_count=self.execution_count,
                    last_updated=datetime.now()
                )

        # Parse the JSON result
        try:
            import json
            data = json.loads(result_text.strip())

            # Convert to VariableInfo objects
            variables = {}
            for var_data in data.get("variables", []):
                var_info = VariableInfo(
                    name=var_data["name"],
                    var_type=var_data.get("var_type", "unknown"),
                    shape=var_data.get("shape"),
                    length=var_data.get("length"),
                    columns=var_data.get("columns"),
                    value_preview=var_data.get("value_preview"),
                    dtype=var_data.get("dtype")
                )
                variables[var_info.name] = var_info

            return KernelState(
                variables=variables,
                is_alive=True,
                execution_count=self.execution_count,
                last_updated=datetime.now()
            )

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse kernel state: {e}")
            return KernelState(
                is_alive=True,
                execution_count=self.execution_count,
                last_updated=datetime.now()
            )


class KernelRegistry:
    """
    Global registry of running kernels.

    Manages kernel lifecycle across the application.
    Keyed by notebook path for proper isolation.
    """

    _kernels: Dict[str, NotebookKernel] = {}
    _lock: Optional[asyncio.Lock] = None

    @classmethod
    def _get_lock(cls) -> asyncio.Lock:
        """Lazily create the lock in the current event loop."""
        if cls._lock is None:
            cls._lock = asyncio.Lock()
        return cls._lock

    # Idle timeout (30 minutes)
    IDLE_TIMEOUT = timedelta(minutes=30)

    @classmethod
    async def get_kernel(
        cls,
        notebook_path: str,
        working_dir: str,
        kernel_name: str = "python3",
    ) -> NotebookKernel:
        """
        Get or create kernel for a notebook.

        Args:
            notebook_path: Path to the notebook (used as registry key)
            working_dir: Directory where kernel should run (cwd)
            kernel_name: Jupyter kernel spec name ("python3" or "ir")

        Returns:
            NotebookKernel instance
        """
        async with cls._get_lock():
            kernel = cls._kernels.get(notebook_path)

            if kernel:
                if kernel.is_alive():
                    logger.debug(f"Reusing existing kernel for {notebook_path}")
                    return kernel
                else:
                    logger.warning(f"Kernel for {notebook_path} died, restarting...")
                    await cls._cleanup_kernel(notebook_path)

            # Create new kernel with the requested kernel spec
            logger.info(f"Creating new '{kernel_name}' kernel for {notebook_path}")
            kernel = NotebookKernel(notebook_path, working_dir, kernel_name=kernel_name)
            await kernel.start()
            cls._kernels[notebook_path] = kernel

            return kernel

    @classmethod
    async def stop_kernel(cls, notebook_path: str) -> None:
        """Stop kernel for a specific notebook."""
        async with cls._get_lock():
            await cls._cleanup_kernel(notebook_path)

    @classmethod
    async def _cleanup_kernel(cls, notebook_path: str) -> None:
        """Internal cleanup (must be called with lock held)."""
        kernel = cls._kernels.pop(notebook_path, None)
        if kernel:
            await kernel.stop()

    @classmethod
    async def stop_all(cls) -> None:
        """Stop all kernels (for shutdown)."""
        async with cls._get_lock():
            paths = list(cls._kernels.keys())
            for path in paths:
                await cls._cleanup_kernel(path)

            logger.info("All kernels stopped")

    @classmethod
    async def cleanup_idle_kernels(cls) -> int:
        """
        Stop kernels that have been idle too long.

        Returns number of kernels cleaned up.
        """
        async with cls._get_lock():
            cleaned = 0
            paths_to_cleanup = []

            for path, kernel in cls._kernels.items():
                if kernel.get_idle_time() > cls.IDLE_TIMEOUT:
                    paths_to_cleanup.append(path)

            for path in paths_to_cleanup:
                await cls._cleanup_kernel(path)
                cleaned += 1

            if cleaned > 0:
                logger.info(f"Cleaned up {cleaned} idle kernel(s)")

            return cleaned

    @classmethod
    def get_active_count(cls) -> int:
        """Get number of active kernels."""
        return len(cls._kernels)

    @classmethod
    def list_kernels(cls) -> List[Dict[str, Any]]:
        """List all active kernels with info."""
        result = []
        for path, kernel in cls._kernels.items():
            result.append({
                "notebook_path": path,
                "working_dir": kernel.working_dir,
                "started_at": kernel.started_at.isoformat() if kernel.started_at else None,
                "idle_time_seconds": kernel.get_idle_time().total_seconds(),
                "execution_count": kernel.execution_count,
                "is_alive": kernel.is_alive()
            })
        return result
