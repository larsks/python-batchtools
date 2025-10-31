import sys
from pathlib import Path


def prepare_context(
    context: int, context_dir: str, jobs_dir: str, output_dir: str, getlist_path: str
) -> None:
    if not context:
        return

    ctx = Path(context_dir).resolve()
    out = Path(output_dir).resolve()
    gl = Path(getlist_path).resolve()
    jobs = Path(jobs_dir).resolve()

    if not ctx.is_dir():
        sys.exit(f"ERROR: CONTEXT_DIR: {ctx} is not a directory")

    if out.exists():
        sys.exit(f"ERROR: {out} directory already exists")
    try:
        out.mkdir(parents=True, exist_ok=False)
    except FileExistsError:
        sys.exit("ERROR: Failed to make output dir (already exists)")
    except Exception as e:
        sys.exit(f"ERROR: Failed to make output dir: {e}")

    jdir_rel: str | None = None
    # Is jobs_dir directly under context_dir? if yes create relative path of jobs
    if jobs.parent.resolve() == ctx:
        jdir_rel = f"./{jobs.name}"
    else:
        jdir_rel = None

    entries: list[str] = []
    for name in sorted(p.name for p in ctx.iterdir()):
        # immediate children only (like -mindepth 1 -maxdepth 1)
        # "find" would include both files and directories; do the same here
        rel = f"./{name}"
        if jdir_rel and rel == jdir_rel:
            continue
        entries.append(rel)

    # write files to get list
    try:
        gl.parent.mkdir(parents=True, exist_ok=True)
        gl.write_text("\n".join(entries) + ("\n" if entries else ""))
    except Exception as e:
        print(f"ERROR: Failed to write getlist at {gl}: {e}")
        sys.exit(1)
