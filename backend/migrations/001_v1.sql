-- V1 schema (MASTER_SPEC.md §5)
CREATE TABLE users (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL DEFAULT 'me',
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE sessions (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id),
  source TEXT NOT NULL DEFAULT 'desktop',
  started_at TEXT NOT NULL DEFAULT (datetime('now')),
  ended_at TEXT,
  turn_count INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE turns (
  id INTEGER PRIMARY KEY,
  session_id INTEGER NOT NULL REFERENCES sessions(id),
  user_id INTEGER NOT NULL REFERENCES users(id),
  role TEXT NOT NULL,
  text TEXT NOT NULL,
  t_wake_ms INTEGER,
  t_eot_ms INTEGER,
  t_first_audio_ms INTEGER,
  latency_ms INTEGER,
  created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE costs (
  id INTEGER PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id),
  day TEXT NOT NULL,
  provider TEXT NOT NULL,
  audio_seconds REAL NOT NULL DEFAULT 0,
  tokens_in INTEGER NOT NULL DEFAULT 0,
  tokens_out INTEGER NOT NULL DEFAULT 0,
  usd_cents REAL NOT NULL DEFAULT 0
);

CREATE TABLE settings (
  user_id INTEGER NOT NULL REFERENCES users(id),
  key TEXT NOT NULL,
  value TEXT NOT NULL,
  PRIMARY KEY (user_id, key)
);

INSERT OR IGNORE INTO users (id, name) VALUES (1, 'me');
