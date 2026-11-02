"""Run dbt using the database URL from .env.   Usage:  python run_dbt.py build"""
import os
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import unquote, urlparse

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

url = urlparse(os.environ["SUPABASE_DB_URL"])
os.environ.update(
    DBT_HOST=url.hostname,
    DBT_PORT=str(url.port or 5432),
    DBT_USER=unquote(url.username or ""),
    DBT_PASSWORD=unquote(url.password or ""),
    DBT_DBNAME=(url.path or "/postgres").lstrip("/") or "postgres",
)

dbt = shutil.which("dbt") or "dbt"
cmd = [dbt, *sys.argv[1:], "--project-dir", "airwatch_dbt", "--profiles-dir", "airwatch_dbt"]
sys.exit(subprocess.call(cmd, cwd=ROOT))
