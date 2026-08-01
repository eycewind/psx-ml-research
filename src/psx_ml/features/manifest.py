from __future__ import annotations

import hashlib
import json
import platform
import subprocess
from datetime import datetime,timezone
from pathlib import Path

import numpy
import pyarrow
import pyarrow.ipc as ipc


def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda:f.read(1024*1024),b""): h.update(block)
    return h.hexdigest()


def logical_hash(table) -> str:
    sink=pyarrow.BufferOutputStream()
    with ipc.new_stream(sink,table.schema) as writer: writer.write_table(table)
    return hashlib.sha256(sink.getvalue().to_pybytes()).hexdigest()


def git_state(repo: Path) -> dict:
    try:
        sha=subprocess.run(["git","-C",str(repo),"rev-parse","HEAD"],check=True,capture_output=True,text=True).stdout.strip()
        dirty=bool(subprocess.run(["git","-C",str(repo),"status","--porcelain"],check=True,capture_output=True,text=True).stdout)
        return {"commit":sha,"dirty":dirty}
    except Exception: return {"commit":"unavailable","dirty":None}


def write_json(value: dict,path: Path) -> None:
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(value,indent=2,sort_keys=True)+"\n"); tmp.replace(path)


def runtime_versions() -> dict:
    return {"python":platform.python_version(),"numpy":numpy.__version__,"pyarrow":pyarrow.__version__}
