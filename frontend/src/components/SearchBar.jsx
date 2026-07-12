export default function SearchBar({ value, onChange, onSubmit, loading }) {
  return (
    <form
      className="search-form"
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit();
      }}
    >
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Search your notes…"
        autoFocus
      />
      <button type="submit" disabled={loading || !value.trim()}>
        {loading ? "Searching…" : "Search"}
      </button>
    </form>
  );
}
