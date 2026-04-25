const DEMO_QUERIES = [
  "I've been charged twice this month and nobody is responding to my emails",
  "My account has been hacked and I can't log in — please help ASAP!!!",
  "Your app has been broken for 3 days and I need a refund immediately",
  "When will my order arrive? It's been 2 weeks",
];

export function QueryInput({ query, onChange, onSubmit, loading }) {
  function handleKey(e) {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) onSubmit();
  }

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-slate-200 p-8">
      <label className="block text-sm font-semibold text-slate-700 mb-2">
        Customer complaint
      </label>
      <textarea
        rows={3}
        value={query}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKey}
        placeholder="Type a customer complaint, or pick one below…"
        className="w-full border border-slate-300 rounded-lg px-4 py-3 text-base resize-none focus:ring-2 focus:ring-brand-500 focus:border-brand-500"
      />
      <div className="flex flex-wrap gap-2 mt-3 mb-5">
        <span className="text-xs text-slate-500 self-center">Try:</span>
        {DEMO_QUERIES.map((q) => (
          <button
            key={q}
            onClick={() => onChange(q)}
            className="text-xs px-2 py-1 rounded bg-slate-100 hover:bg-slate-200 text-slate-700 text-left"
          >
            {q.length > 55 ? q.slice(0, 55) + '…' : q}
          </button>
        ))}
      </div>
      <button
        onClick={onSubmit}
        disabled={loading || !query.trim()}
        className="w-full bg-brand-600 hover:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-3 rounded-lg transition shadow-sm"
      >
        {loading ? (
          <span className="inline-block pulse-soft">⏳ Running all four models…</span>
        ) : (
          'Submit complaint'
        )}
      </button>
      <p className="text-xs text-slate-400 text-center mt-2">Ctrl+Enter to submit</p>
    </div>
  );
}