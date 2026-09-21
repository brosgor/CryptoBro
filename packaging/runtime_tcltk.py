# Runtime hook: apunta Tcl/Tk 9 embebidos (build uv) dentro del bundle PyInstaller.
import os
import sys


def _meipass() -> str:
    return getattr(sys, "_MEIPASS", "")


base = _meipass()
if base:
    tcl = os.path.join(base, "tcl9.0")
    tk = os.path.join(base, "tk9.0")
    if os.path.isdir(tcl):
        os.environ.setdefault("TCL_LIBRARY", tcl)
    if os.path.isdir(tk):
        os.environ.setdefault("TK_LIBRARY", tk)
    # .so de Tcl/Tk 9 van en la raíz del bundle
    os.environ["LD_LIBRARY_PATH"] = base + os.pathsep + os.environ.get("LD_LIBRARY_PATH", "")
