import { useState } from "react";
import SearchBar from "./components/SearchBar.jsx";
import ResultCard from "./components/ResultCard.jsx";

export default function App() {
  const [query, setQuery] = useState("");
  const [submittedQuery, setSubmittedQuery] = useState("");
  const [results, setResults] = useState(null); // null = no search yet
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [folderPath, setFolderPath] = useState("");
  const [indexStatus, setIndexStatus] = useState(null); // { text, error }
  const [indexing, setIndexing] = useState(false);

  async function runSearch() {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    setSubmittedQuery(query);
    try {
      const res = await fetch(`/api/search?q=${encodeURIComponent(query)}&top_k=10`);
      if (!res.ok) throw new Error(`Search failed (${res.status})`);
      const data = await res.json();
      setResults(data.results);
    } catch (e) {
      setError(e.message);
      setResults(null);
    } finally {
      setLoading(false);
    }
  }

  async function runIngest() {
    setIndexing(true);
    setIndexStatus(null);
    try {
      const res = await fetch("/api/ingest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ folder_path: folderPath || null }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Indexing failed");
      setIndexStatus({
        text: `indexed ${data.ingested} note(s), ${data.chunks} chunk(s), ${data.skipped_unchanged} unchanged`,
        error: false,
      });
    } catch (e) {
      setIndexStatus({ text: e.message, error: true });
    } finally {
      setIndexing(false);
    }
  }

  return (
    <div className="app-shell">
      <div className="eyebrow">local index</div>
      <h1 className="title">Search your notes</h1>
      <p className="subtitle">
        Hybrid keyword + semantic search over the markdown notes on your own
        machine. Nothing here leaves your computer.
      </p>

      <SearchBar value={query} onChange={setQuery} onSubmit={runSearch} loading={loading} />

      <div className="index-strip">
        <span>index a folder:</span>
        <input
          type="text"
          value={folderPath}
          onChange={(e) => setFolderPath(e.target.value)}
          placeholder="defaults to server config"
        />
        <button onClick={runIngest} disabled={indexing}>
          {indexing ? "indexing…" : "run ingest"}
        </button>
        {indexStatus && (
          <span className={`status ${indexStatus.error ? "error" : ""}`}>
            {indexStatus.text}
          </span>
        )}
      </div>

      {error && (
        <div className="state-block">
          <div className="headline">Something went wrong</div>
          {error}
        </div>
      )}

      {!error && results !== null && (
        <div className="results">
          <div className="results-count">
            {results.length} result{results.length === 1 ? "" : "s"} for “{submittedQuery}”
          </div>
          {results.length === 0 && (
            <div className="state-block">
              <div className="headline">No matches</div>
              Try different words, or index a folder first if you haven't yet.
            </div>
          )}
          {results.map((r) => (
            <ResultCard key={r.chunk_id} result={r} query={submittedQuery} />
          ))}
        </div>
      )}

      {!error && results === null && (
        <div className="state-block">
          <div className="headline">Nothing searched yet</div>
          Index a folder of markdown notes above, then search for a word, phrase, or
          idea — matches on meaning show up even without the exact words.
        </div>
      )}
    </div>
  );
}
