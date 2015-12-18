import os
import time
import sqlite3
from contextlib import closing
import config


def init_db():
    with closing(get_db()) as db:
        schema_path = os.path.join(config.Config["app_path"], "schema.sql")
        with open(schema_path, "r") as f:
            db.executescript(f.read())
        db.commit()


def get_db():
    conn = sqlite3.connect(config.Config["dbfile"])
    return conn


def write_log(message, error=False, alarm=False):
    with closing(get_db()) as db:
        print(message, flush=True)
        db.cursor().execute(
            "insert into log "
            "(error, alarm, message, log_time) "
            "values (:error, :alarm, :message, :time);",
            {
                "error": error,
                "alarm": alarm,
                "message": message,
                "time": time.time()})
        db.commit()
