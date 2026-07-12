import { useState } from "react";

function highlight(snippet, query) {
  const terms = query
    .split(/\s+/)
    .map((t) => t.replace(/[^A-Za-z0-9_]/g, ""))
    .filter(Boolean);
  if (terms.length === 0) return snippet;
  const pattern = new RegExp(`(${terms.join("|")})`, "ig");
  const parts = snippet.split(pattern);
  return parts.map((part, i) =>
    terms.some((t) => t.toLowerCase() === part.toLowerCase()) ? (
      <mark key={i}>{part}</mark>
    ) : (
      <span key={i}>{part}</span>
    )
  );
}

export default function ResultCard({ result, query }) {
  const [expanded, setExpanded] = useState(false);
  const [note, setNote] = useState(null);
  const [loadingNote, setLoadingNote] = useState(false);

  const matchLabel =
    result.matched_keyword && result.matched_semantic
      ? "both"
      : result.matched_keyword
      ? "keyword"
      : "semantic";

  async function toggleExpand() {
    if (!expanded && !note) {
      setLoadingNote(true);
      try {
        const res = await fetch(`/api/notes/${result.note_id}`);
        if (res.ok) setNote(await res.json());
      } finally {
        setLoadingNote(false);
      }
    }
    setExpanded((v) => !v);
  }

  return (
    <div className="card">
      <h3 className="card-title">
        <a
          href="#"
          onClick={(e) => {
            e.preventDefault();
            toggleExpand();
          }}
        >
          {result.title}
        </a>
      </h3>
      <p className="card-snippet">{highlight(result.snippet, query)}</p>
      <div className="card-meta">
        <span className={`badge ${matchLabel === "both" ? "both" : ""}`}>
          {matchLabel}
        </span>
        <span className="path" title={result.path}>
          {result.path.split("/").pop()}
        </span>
        <span>
          lines {result.start_line}–{result.end_line}
        </span>
        <span>score {result.score}</span>
      </div>

      {expanded && (
        <div style={{ marginTop: 16 }}>
          {loadingNote && <p className="card-snippet">Loading note…</p>}
          {note && (
            <pre
              style={{
                whiteSpace: "pre-wrap",
                background: "var(--panel-raised)",
                border: "1px solid var(--rule)",
                borderRadius: 3,
                padding: 16,
                fontFamily: "var(--mono)",
                fontSize: 13,
                color: "var(--text-dim)",
                maxHeight: 360,
                overflowY: "auto",
              }}
            >
              {note.content}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}
