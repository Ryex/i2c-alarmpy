#!/usr/bin/python
import time
import flask
import database
import utils
from config import Config
from alarm import Alarm
import smbio
app = flask.Flask(__name__)


# =================================================
# Request Context
# =================================================
@app.before_request
def before_request():
    flask.g.db = database.get_db()
    flask.g.title = Config["title"]


@app.teardown_request
def teardown_request(exception):
    db = getattr(flask.g, 'db', None)
    if db is not None:
        db.close()


# =================================================
# Root & Static
# =================================================
@app.route("/")
def root():
    if utils.needs_user():
        return flask.redirect(flask.url_for('setup'))
    if 'logged_in' in flask.session and flask.session['logged_in']:
        return flask.redirect(flask.url_for('dashboard'))
    return flask.redirect(flask.url_for('login'))


@app.route('/js/<path:path>')
def send_j2(path):
    return flask.send_from_directory('js', path)


@app.route('/css/<path:path>')
def send_css(path):
    return flask.send_from_directory('css', path)


@app.route('/img/<path:path>')
def send_img(path):
    return flask.send_from_directory('img', path)


@app.route('/fonts/<path:path>')
def send_font(path):
    return flask.send_from_directory('fonts', path)


# =================================================
# Users
# =================================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if utils.needs_user():
        return flask.redirect(flask.url_for('setup'))
    if 'logged_in' in flask.session and flask.session['logged_in']:
        return flask.redirect(flask.url_for('dashboard'))
    error = None
    if flask.request.method == 'POST':
        username = flask.request.form['username']
        user = utils.get_user(username)
        if user:
            if utils.check_user_pass(user, flask.request.form['password']):
                flask.session['logged_in'] = True
                flask.session['username'] = user
                flask.flash('You were logged in')
                return flask.redirect(flask.url_for('dashboard'))
        error = "Invaid username or password"
    return flask.render_template('login.j2', error=error)


@app.route('/logout')
def logout():
    flask.session.pop('logged_in', None)
    flask.flash('You were logged out')
    return flask.redirect(flask.url_for('login'))


@app.route('/users', methods=['GET', 'POST'])
def users():
    if utils.needs_user():
        return flask.redirect(flask.url_for('setup'))
    if ('logged_in' not in flask.session) or (not flask.session['logged_in']):
        return flask.redirect(flask.url_for('login'))

    error = None
    if flask.request.method == 'POST':
        if "delete" in flask.request.form:
            if len(utils.get_users()) > 1:
                user_id = int(flask.request.form['id'])
                utils.delete_user(user_id)
                flask.flash('User Deleted')
            else:
                flask.flash("can not delete last user")
        else:
            username = flask.request.form['username']
            user = utils.get_user()
            if not user:
                password = flask.request.form['password']
                password_confirm = flask.request.form['password_confirm']
                if password == password_confirm:
                    utils.create_user(username, password)
                    flask.flash('User Created')
                    return flask.redirect(flask.url_for('login'))
                error = "passwords do not match"
            else:
                error = "user already exists"

    users = utils.get_users()
    return flask.render_template(
        'users.j2',
        users=users,
        error=error)


# =================================================
# Setup
# =================================================
@app.route('/setup', methods=['GET', 'POST'])
def setup():
    if not utils.needs_user():
        return flask.redirect(flask.url_for('login'))
    error = None
    if flask.request.method == 'POST':
        username = flask.request.form['username']
        password = flask.request.form['password']
        password_confirm = flask.request.form['password_confirm']
        if password == password_confirm:
            utils.create_user(username, password)
            flask.flash('User Created')
            return flask.redirect(flask.url_for('login'))
        error = "passwords do not match"
    return flask.render_template('setup.j2', error=error)


# =================================================
# Dashboard
# =================================================
@app.route('/dashboard')
def dashboard():
    if utils.needs_user():
        return flask.redirect(flask.url_for('setup'))
    if ('logged_in' not in flask.session) or (not flask.session['logged_in']):
        return flask.redirect(flask.url_for('login'))
    running = utils.check_pid(Config["pidfile"])
    trunning, tutime = utils.get_last_manager_state()
    tutime_s = ""
    if tutime:
        tutime_s = time.strftime("%c", time.localtime(tutime))

    thread_state = {
        "running": trunning,
        "utime": tutime_s
    }

    utime = time.strftime("%c", time.localtime())
    state_text = "Not Runnning"
    flags = {
        "alarm": False,
        "armed": False,
        "disarmed": False,
        "tripped": False,
        "falted": False,
    }

    state_data = None

    state = utils.get_latest_state()
    if state_data:
        alarm_state, state_data, state_time_i = state
        utime = time.strftime("%c", time.localtime(state_time_i))
        state_text = Alarm.ALARM_STATES[alarm_state]
        flags["alarm"] = alarm_state == Alarm.ALARMED
        flags["disarmed"] = alarm_state == Alarm.DISARMED
        flags["tripped"] = alarm_state == Alarm.TRIPPED
        flags["falted"] = alarm_state == Alarm.FALT
        flags["armed"] = alarm_state == Alarm.ARMED

    interfaces = utils.get_interfaces()
    return flask.render_template(
        'dashboard.j2',
        flags=flags,
        running=running,
        thread_state=thread_state,
        state_text=state_text,
        state_data=state_data,
        utime=utime,
        interfaces=interfaces,
        smbio=smbio)


# =================================================
# Logs
# =================================================
@app.template_filter('format_local_time')
def format_local_time(t):
    return time.strftime("%c", time.localtime(t))


@app.route('/logs')
def logs():
    if utils.needs_user():
        return flask.redirect(flask.url_for('setup'))
    if ('logged_in' not in flask.session) or (not flask.session['logged_in']):
        return flask.redirect(flask.url_for('login'))
    logs = utils.get_logs()
    return flask.render_template(
        'logs.j2',
        mode="logs",
        logs=logs)


@app.route('/errors')
def logs_errors():
    if utils.needs_user():
        return flask.redirect(flask.url_for('setup'))
    if ('logged_in' not in flask.session) or (not flask.session['logged_in']):
        return flask.redirect(flask.url_for('login'))
    logs = utils.get_logs_errors()
    return flask.render_template(
        'logs.j2',
        mode="errors",
        logs=logs)


@app.route('/alarms')
def logs_alarms():
    if utils.needs_user():
        return flask.redirect(flask.url_for('setup'))
    if ('logged_in' not in flask.session) or (not flask.session['logged_in']):
        return flask.redirect(flask.url_for('login'))
    logs = utils.get_logs_errors()
    return flask.render_template(
        'logs.j2',
        mode="alarms",
        logs=logs)


# =================================================
# Alarm Actions
# =================================================
@app.route("/start", methods=['POST'])
def start():
    if 'logged_in' in flask.session and flask.session['logged_in']:
        utils.write_command({"start": "Web Interface Start"})
        return flask.redirect(flask.url_for('dashboard'))
    return flask.abort(403)


@app.route("/stop", methods=['POST'])
def stop():
    if 'logged_in' in flask.session and flask.session['logged_in']:
        utils.write_command({"stop": "Web Interface Stop"})
        return flask.redirect(flask.url_for('dashboard'))
    return flask.abort(403)


@app.route("/restart", methods=['POST'])
def restart():
    if 'logged_in' in flask.session and flask.session['logged_in']:
        utils.write_command({"restart": "Web Interface Restart"})
        return flask.redirect(flask.url_for('dashboard'))
    return flask.abort(403)


@app.route("/arm", methods=['POST'])
def arm():
    if 'logged_in' in flask.session and flask.session['logged_in']:
        utils.write_command({"action": {"arm": "Web Interface Arm"}})
        return flask.redirect(flask.url_for('dashboard'))
    return flask.abort(403)


@app.route("/disarm", methods=['POST'])
def disarm():
    if 'logged_in' in flask.session and flask.session['logged_in']:
        utils.write_command({"action": {"disarm": "Web Interface Disarm"}})
        return flask.redirect(flask.url_for('dashboard'))
    return flask.abort(403)


@app.route("/alarm", methods=['POST'])
def alarm():
    if 'logged_in' in flask.session and flask.session['logged_in']:
        utils.write_command({"action": {"alarm": "Web Interface Alarm"}})
        return flask.redirect(flask.url_for('dashboard'))
    return flask.abort(403)


# =================================================
# Alarm Configuration
# =================================================
@app.route("/io", methods=['GET', 'POST'])
def io_config():
    if utils.needs_user():
        return flask.redirect(flask.url_for('setup'))
    if ('logged_in' not in flask.session) or (not flask.session['logged_in']):
        return flask.redirect(flask.url_for('login'))

    error = None
    if flask.request.method == 'POST':
        if "delete" in flask.request.form:
            io_id = int(flask.request.form['id'])
            utils.delete_io(io_id)
            flask.flash('IO Deleted')
        else:
            io_type = int(flask.request.form['type'])
            bus = int(flask.request.form['bus'])
            addr = int(flask.request.form['addr'], 16)
            utils.create_io(io_type, bus, addr)
            flask.flash('IO Created')

    ios = utils.get_ios()
    return flask.render_template(
        'io_config.j2',
        error=error,
        ios=ios,
        smbio=smbio)


@app.route("/interface", methods=['GET', 'POST'])
def interface_config():
    if utils.needs_user():
        return flask.redirect(flask.url_for('setup'))
    if ('logged_in' not in flask.session) or (not flask.session['logged_in']):
        return flask.redirect(flask.url_for('login'))

    error = None
    if flask.request.method == 'POST':
        if "delete" in flask.request.form:
            interface_id = int(flask.request.form['id'])
            utils.delete_interface(interface_id)
            flask.flash('Interface Deleted')
        else:
            interface_type = int(flask.request.form['type'])
            io_id = int(flask.request.form['io_id'])
            slot = int(flask.request.form['slot'])
            datamap = smbio.INTERFACEDATAMAP[interface_type]
            data = {}
            for key in datamap:
                data[key] = flask.request.form[key]
            utils.create_interface(interface_type, io_id, slot, data)
            flask.flash('Interface Created')

    interfaces = utils.get_interfaces()
    ios = utils.get_ios()
    return flask.render_template(
        'interface_config.j2',
        error=error,
        interfaces=interfaces,
        ios=ios,
        smbio=smbio)


@app.route('/action', methods=['GET', 'POST'])
def action_config():
    if utils.needs_user():
        return flask.redirect(flask.url_for('setup'))
    if ('logged_in' not in flask.session) or (not flask.session['logged_in']):
        return flask.redirect(flask.url_for('login'))

    error = None
    if flask.request.method == 'POST':
        if "delete" in flask.request.form:
            action_id = int(flask.request.form['id'])
            utils.delete_action(action_id)
            flask.flash('Action Deleted')
        else:
            code = flask.request.form['code']
            cmd = flask.request.form['cmd']
            reason = flask.request.form['reason']
            utils.create_action(code, cmd, reason)
            flask.flash('Action Created')

    actions = utils.get_actions()
    return flask.render_template(
        'action_config.j2',
        error=error,
        actions=actions,
        commands=Alarm.ACTIONS)


@app.route("/indicator", methods=['GET', 'POST'])
def indicator_config():
    if utils.needs_user():
        return flask.redirect(flask.url_for('setup'))
    if ('logged_in' not in flask.session) or (not flask.session['logged_in']):
        return flask.redirect(flask.url_for('login'))

    error = None
    if flask.request.method == 'POST':
        if "delete" in flask.request.form:
            indicator_id = int(flask.request.form['id'])
            utils.delete_indicator(indicator_id)
            flask.flash('Indicaor Deleted')
        else:
            interface_id = int(flask.request.form["interface_id"])
            state = int(flask.request.form["state"])
            utils.create_indicator(interface_id, state)
            flask.flash('Indicator Created')

    interfaces = utils.get_interfaces()
    indicators = utils.get_indicators()
    return flask.render_template(
        'indicator_config.j2',
        error=error,
        interfaces=interfaces,
        indicators=indicators,
        alarm_states=Alarm.ALARM_STATES)


if __name__ == "__main__":
    database.init_db()
    app.secret_key = Config["secret"]
    app.run(
        host=Config["host"],
        port=Config["port"],
        debug=Config["debug"])
