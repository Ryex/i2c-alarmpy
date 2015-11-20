import os
import json
import flask
import bcrypt


def check_pid(pidfile):
    if os.path.exists(pidfile):
        try:
            with open(pidfile, "r") as f:
                pid = f.read()
            return os.path.exists(os.path.join("/proc", pid))
        except OSError:
            pass
    return False


def needs_user():
    c = flask.g.db.cursor()
    c.execute("select user_id from user;")
    if c.fetchone():
        return False
    return True


def get_user(username):
    c = flask.g.db.cursor()
    c.execute(
        "select user_id, username, pw_hash from user where username = ?;",
        (username,))
    result = c.fetchone()
    if result:
        user_id, username, pw_hash = result
        return {
            "user_id": user_id,
            "username": username,
            "pw_hash": pw_hash
        }
    return None


def get_users():
    c = flask.g.db.cursor()
    c.execute("select user_id, username from user order by user_id ASC;")
    rows = c.fetchall()
    if rows:
        users = []
        for user in rows:
            user_id, username = user
            users.append({
                "user_id": user_id,
                "username": username
            })
        return users
    return None


def check_user_pass(user, password):
    pw_hash = bcrypt.hashpw(
        password.encode('UTF-8'),
        user["pw_hash"].encode('UTF-8')
    ).decode('UTF-8')
    if pw_hash == user["pw_hash"]:
        return True
    return False


def create_user(username, password):
    user = {
        "username": username,
        "pw_hash": bcrypt.hashpw(
            password.encode('UTF-8'),
            bcrypt.gensalt()
        ).decode('UTF-8')
    }
    c = flask.g.db.cursor()
    c.execute(
        "insert into user (username, pw_hash) values "
        "(:username, :pw_hash)",
        user)
    flask.g.db.commit()


def delete_user(user_id):
    c = flask.g.db.cursor()
    c.execute(
        "delete from user "
        "where user_id = ?;",
        str(user_id))
    flask.g.db.commit()


def get_latest_state():
    c = flask.g.db.cursor()
    c.execute(
        "select state, data, state_time "
        "from state "
        "order by state_time DESC limit 1;")
    state = c.fetchone()
    istate = None
    state_time = None
    data = None
    if state:
        istate, data_s, state_time = state
        data = json.loads(data_s)
    return (istate, data, state_time)


def get_last_manager_state():
    c = flask.g.db.cursor()
    c.execute(
        "select state, state_time "
        "from manager_state "
        "order by state_time DESC limit 1;")
    state = c.fetchone()
    if state:
        return state
    return (None, None)


def get_ios():
    c = flask.g.db.cursor()
    c.execute(
        "select io_id, type, bus, addr "
        "from io "
        "order by io_id ASC;")
    rows = c.fetchall()
    ios = []
    for row in rows:
        io_id, io_type, bus, addr = row
        ios.append({
            "io_id": io_id,
            "type": io_type,
            "bus": bus,
            "addr": addr,
            "addr_hex": hex(addr)
        })
    return ios


def create_io(io_type, bus, addr):
    c = flask.g.db.cursor()
    c.execute(
        "insert into io "
        "(type, bus, addr) "
        "values (:io_type, :bus, :addr);",
        {"io_type": io_type, "bus": bus, "addr": addr})
    flask.g.db.commit()


def delete_io(io_id):
    c = flask.g.db.cursor()
    c.execute(
        "delete from io "
        "where io_id = ?;",
        str(io_id))
    flask.g.db.commit()


def get_interfaces():
    c = flask.g.db.cursor()
    c.execute(
        "select interface_id, type, io_id, slot, data "
        "from interface "
        "order by interface_id ASC;")
    rows = c.fetchall()
    interfaces = []
    for row in rows:
        interface_id, interface_type, io_id, slot, data_s = row
        data = json.loads(data_s)
        interfaces.append({
            "interface_id": interface_id,
            "type": interface_type,
            "io_id": io_id,
            "slot": slot,
            "data": data
        })
    return interfaces


def create_interface(interface_type, io_id, slot, data):
    c = flask.g.db.cursor()
    c.execute(
        "insert into interface "
        "(type, io_id, slot, data) "
        "values (:interface_type, :io_id, :slot, :data);",
        {
            "interface_type": interface_type,
            "io_id": io_id,
            "slot": slot,
            "data": json.dumps(data),
        })
    flask.g.db.commit()


def delete_interface(interface_id):
    c = flask.g.db.cursor()
    c.execute(
        "delete from interface "
        "where interface_id = ?;",
        str(interface_id))
    flask.g.db.commit()


def get_indicators():
    c = flask.g.db.cursor()
    c.execute(
        "select indicator_id, interface_id, state "
        "from indicator "
        "order by indicator_id ASC;")
    rows = c.fetchall()
    indicators = []
    for row in rows:
        indicator_id, interface_id, state = row
        indicators.append({
            "indicator_id": indicator_id,
            "interface_id": interface_id,
            "state": state
        })
    return indicators


def create_indicator(interface_id, state):
    c = flask.g.db.cursor()
    c.execute(
        "insert into indicator "
        "(interface_id, state) "
        "values (:interface_id, :state);",
        {
            "interface_id": interface_id,
            "state": state
        })
    flask.g.db.commit()


def delete_indicator(indicator_id):
    c = flask.g.db.cursor()
    c.execute(
        "delete from indicator "
        "where indicator_id = ?;",
        str(indicator_id))
    flask.g.db.commit()


def get_actions():
    c = flask.g.db.cursor()
    c.execute(
        "select action_id, code_hash, command, reason "
        "from action "
        "order by action_id ASC;")
    rows = c.fetchall()
    actions = []
    for row in rows:
        action_id, code_hash, command, reason = row
        actions.append({
            "action_id": action_id,
            "code_hash": code_hash,
            "command": command,
            "reason": reason
        })
    return actions


def create_action(code, command, reason):
    code_hash = bcrypt.hashpw(
        code.encode('UTF-8'),
        bcrypt.gensalt()
        ).decode('UTF-8')
    c = flask.g.db.cursor()
    c.execute(
        "insert into action "
        "(code_hash, command, reason) "
        "values (:code_hash, :command, :reason);",
        {
            "code_hash": code_hash,
            "command": command,
            "reason": reason
        })
    flask.g.db.commit()


def delete_action(action_id):
    c = flask.g.db.cursor()
    c.execute(
        "delete from action "
        "where action_id = ?;",
        str(action_id))
    flask.g.db.commit()


def get_logs():
    c = flask.g.db.cursor()
    c.execute(
        "select log_id, error, alarm, message, log_time "
        "from log "
        "order by log_time DESC;")
    rows = c.fetchall()
    logs = []
    for row in rows:
        log_id, error, alarm, message, log_time = row
        logs.append({
            "log_id": log_id,
            "error": error,
            "alarm": alarm,
            "message": message,
            "log_time": log_time
        })
    return logs


def get_logs_errors():
    c = flask.g.db.cursor()
    c.execute(
        "select log_id, error, alarm, message, log_time "
        "from log where error = 1 "
        "order by log_time DESC;")
    rows = c.fetchall()
    logs = []
    for row in rows:
        log_id, error, alarm, message, log_time = row
        logs.append({
            "log_id": log_id,
            "error": error,
            "alarm": alarm,
            "message": message,
            "log_time": log_time
        })
    return logs


def get_logs_alarms():
    c = flask.g.db.cursor()
    c.execute(
        "select log_id, error, alarm, message, log_time "
        "from log where alarm = 1 "
        "order by log_time DESC;")
    rows = c.fetchall()
    logs = []
    for row in rows:
        log_id, error, alarm, message, log_time = row
        logs.append({
            "log_id": log_id,
            "error": error,
            "alarm": alarm,
            "message": message,
            "log_time": log_time
        })
    return logs


def write_command(cmd):
    c = flask.g.db.cursor()
    c.execute(
        "insert into cmdq "
        "(data) "
        "values (:data);",
        {
            "data": json.dumps(cmd)
        })
    flask.g.db.commit()
