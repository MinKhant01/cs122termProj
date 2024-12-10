DROP TABLE IF EXISTS alarms;

CREATE TABLE IF NOT EXISTS alarms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hour TEXT NOT NULL,
    minute TEXT NOT NULL,
    am_pm TEXT CHECK(am_pm IN ('AM', 'PM')) NOT NULL,
    label TEXT,
    repeat TEXT CHECK(repeat IN ('None', 'Every Sunday', 'Every Monday', 'Every Tuesday', 'Every Wednesday', 'Every Thursday', 'Every Friday', 'Every Saturday')) NOT NULL DEFAULT 'None',
    active INTEGER NOT NULL DEFAULT 1
);
