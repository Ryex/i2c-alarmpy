import os
import json

app_path = os.path.dirname(os.path.realpath(__file__))
Config = None
try:
    cfg_path = os.path.join(app_path, "config.json")
    with open(cfg_path, 'r') as f:
        Config = json.load(f)

except Exception:
    pass

if not isinstance(Config, dict):
    Config = {}

Config["app_path"] = app_path
del app_path

if "dbfile" not in Config:
    Config["dbfile"] = "alarm.db"

if "host" not in Config:
    Config["host"] = "0.0.0.0"

if "port" not in Config:
    Config["port"] = 65432

if "debug" not in Config:
    Config["debug"] = False

if "tripped_timeout" not in Config:
    Config["tripped_timeout"] = 30

if "falted_timeout" not in Config:
    Config["falted_timeout"] = 10

if "secret" not in Config:
    Config["secret"] = None

if "title" not in Config:
    Config["title"] = "Alarm System"

if "pidfile" not in Config:
    Config["pidfile"] = "/var/run/alarmsystem.pid"

if "manager_sleep" not in Config:
    Config["manager_sleep"] = 1

if "alarm_sleep" not in Config:
    Config["alarm_sleep"] = 0
