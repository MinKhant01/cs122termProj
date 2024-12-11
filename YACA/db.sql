SET SESSION sql_notes = 0; -- Disable warnings

CREATE DATABASE IF NOT EXISTS YACA;

USE YACA;

CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS alarms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    hour TEXT NOT NULL,
    minute TEXT NOT NULL,
    am_pm TEXT NOT NULL,
    label TEXT,
    repeat_option TEXT NOT NULL DEFAULT 'None',
    active INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS countdowns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    hours INTEGER NOT NULL,
    minutes INTEGER NOT NULL,
    seconds INTEGER NOT NULL,
    label TEXT,
    active INTEGER NOT NULL DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

SET SESSION sql_notes = 1; -- Enable warnings
