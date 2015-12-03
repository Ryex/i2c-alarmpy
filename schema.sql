create table if not exists user (
    user_id integer primary key autoincrement,
    username text not null,
    pw_hash text not null
);

create table if not exists cmdq (
    cmd_id integer primary key autoincrement,
    data text not null
);

create table if not exists io (
    io_id integer primary key autoincrement,
    type integer not null,
    bus integer not null,
    addr integer not null
);

create table if not exists interface (
    interface_id integer primary key autoincrement,
    type integer not null,
    io_id integer not null,
    slot integer not null,
    data text not null
);

create table if not exists log (
    log_id integer primary key autoincrement,
    error integer not null,
    alarm integer not null,
    message text not null,
    log_time integer not null
);

create table if not exists action (
    action_id integer primary key autoincrement,
    code_hash text not null,
    command text not null,
    reason text not null
);

create table if not exists indicator (
    indicator_id integer primary key autoincrement,
    interface_id integer not null,
    state integer not null
);

create table if not exists state (
    key text unique primary key,
    data text not null,
    state_time integer not null
);
