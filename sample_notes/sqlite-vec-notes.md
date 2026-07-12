---
title: Notes on sqlite-vec
---

# Notes on sqlite-vec

sqlite-vec is a SQLite extension for storing and querying vector embeddings
directly inside a SQLite database. It ships as a small, dependency-free
C extension and works on Linux, macOS, and Windows.

## Why it fits a local-first app

Because everything lives in one .db file, there's no separate vector
database server to run, back up, or keep in sync. That matches the
local-first philosophy: your data stays on your machine, in a format you
can copy, version, or inspect with any SQLite tool.

## Basic usage

You create a virtual table with `CREATE VIRTUAL TABLE vec_items USING
vec0(embedding float[384])`, insert rows with a rowid and a serialized
float32 vector, and query nearest neighbors with a `MATCH` clause plus a
`k` parameter.
