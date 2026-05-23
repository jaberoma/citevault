CREATE TABLE IF NOT EXISTS sources (
    id          TEXT PRIMARY KEY,
    kind        TEXT NOT NULL,
    path        TEXT NOT NULL,
    text        TEXT NOT NULL,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS spans (
    id            TEXT PRIMARY KEY,
    source_id     TEXT NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    start_offset  INTEGER NOT NULL,
    end_offset    INTEGER NOT NULL,
    text          TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS structured_entries (
    id           TEXT PRIMARY KEY,
    source_id    TEXT NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
    entry_type   TEXT NOT NULL,
    payload_json TEXT NOT NULL
);

CREATE VIRTUAL TABLE IF NOT EXISTS spans_fts USING fts5(
    span_id UNINDEXED,
    text,
    tokenize = 'porter unicode61'
);

CREATE VIRTUAL TABLE IF NOT EXISTS spans_vec USING vec0(
    span_id TEXT PRIMARY KEY,
    embedding FLOAT[384]
);

CREATE TABLE IF NOT EXISTS settings (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tailoring_traces (
    id           TEXT PRIMARY KEY,
    started_at   TEXT NOT NULL,
    trace_json   TEXT NOT NULL
);
