DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS payments;

CREATE TABLE user (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL
);

CREATE TABLE payment (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  student_id INTEGER NOT NULL,
  created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  tittle TEXT NOT NULL,
  comment TEXT NOT NULL,
  FOREIGN KEY (student_id) REFERENCES user (id)
);