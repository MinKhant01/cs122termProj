SET SESSION sql_notes = 0; -- Disable warnings

DROP DATABASE IF EXISTS YACA;

CREATE DATABASE YACA;

USE YACA;

DROP TABLE IF EXISTS alarms;
DROP TABLE IF EXISTS users;

SET SESSION sql_notes = 1; -- Enable warnings

CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(255) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS alarms (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    hour VARCHAR(2) NOT NULL,
    minute VARCHAR(2) NOT NULL,
    am_pm ENUM('AM', 'PM') NOT NULL,
    label VARCHAR(255),
    repeat_option ENUM('None', 'Every Sunday', 'Every Monday', 'Every Tuesday', 'Every Wednesday', 'Every Thursday', 'Every Friday', 'Every Saturday') NOT NULL DEFAULT 'None',
    active TINYINT(1) NOT NULL DEFAULT 1,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
