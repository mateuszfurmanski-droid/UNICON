import os
import sys
import traceback
import importlib.util

def _load(py_path: str, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, py_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"spec_from_file_location failed for: {py_path}")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

def _get_app(mod):
    # Prefer a prebuilt Flask app object
    for name in ("app", "application"):
        a = getattr(mod, name, None)
        if a is not None:
            return a

    # Support factory pattern if present
    for name in ("create_app", "make_app"):
        f = getattr(mod, name, None)
        if callable(f):
            return f()

    return None

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Default target is the current master HUD
    target = os.environ.get("UNICON_TARGET", os.path.join(base_dir, "cam_dual_hud_web.py"))
    if not os.path.isabs(target):
        target = os.path.join(base_dir, target)

    host = os.environ.get("UNICON_HOST", "0.0.0.0")
    port = int(os.environ.get("UNICON_PORT", "8095"))

    try:
        mod = _load(target, "unicon_target_app")
        app = _get_app(mod)
        if app is None:
            raise RuntimeError(f"No Flask app found in {target} (expected `app` or `application` or factory).")

        print(f"UNICON_RUNNER_OK target={target} host={host} port={port}", flush=True)

        # MUST be here (runner), NOT inside master module import
        app.run(host=host, port=port, debug=False, use_reloader=False, threaded=True)

    except Exception as e:
        print(f"UNICON_RUNNER_FATAL: {e!r}", flush=True)
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
