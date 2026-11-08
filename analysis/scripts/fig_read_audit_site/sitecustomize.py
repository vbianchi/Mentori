# D155: loads scripts/fig_read_audit.py's audit hook in every Python process S494 starts (S494 puts this folder first
# on PYTHONPATH and sets FIG_READ_AUDIT_DIR). Does nothing when FIG_READ_AUDIT_DIR is unset. Read-only observer.
import os as _os

if _os.environ.get("FIG_READ_AUDIT_DIR"):
    import importlib.util as _u

    _p = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), "fig_read_audit.py")
    _s = _u.spec_from_file_location("_fig_read_audit_hook", _p)
    _m = _u.module_from_spec(_s)
    _s.loader.exec_module(_m)
    _m.install()
