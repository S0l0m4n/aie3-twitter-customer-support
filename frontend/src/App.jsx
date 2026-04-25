import { useState } from 'react';
import { QueryInput } from './components/QueryInput.jsx';
import { AnswerPanel } from './components/AnswerPanel.jsx';
import { SourcePanel } from './components/SourcePanel.jsx';
import { ComparisonTable } from './components/ComparisonTable.jsx';

export default function App() {
  const [query, setQuery] = useState('');
  const [topK, setTopK] = useState(3);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState(null);

  async function submit() {
    const text = query.trim();
    if (!text) return;
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const res = await fetch('/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, top_k: topK }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error ?? `HTTP ${res.status}`);
      setResult(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen">
      <header className="bg-white border-b border-slate-200 sticky top-0 z-20 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4 flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl border-3 border-brand-600 flex items-center justify-center text-xl">
            🎧
          </div>
          <div>
            <h1 className="text-lg font-bold text-slate-900">Twitter Customer Support</h1>
            <p className="text-xs text-slate-500">RAG vs no-RAG answers · ML vs LLM priority prediction</p>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8 space-y-8">
        <QueryInput
          query={query}
          onChange={setQuery}
          onSubmit={submit}
          loading={loading}
          topK={topK}
          onTopKChange={setTopK}
        />

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-800 rounded-xl p-6">
            ❌ {error}
          </div>
        )}

        {result && (
          <>
            <PrioritySummary
              mlLabel={result.ml_prediction.label}
              mlConf={result.ml_prediction.confidence}
              llmLabel={result.llm_prediction.label}
              llmConf={result.llm_prediction.confidence}
            />

            <AnswerPanel
              ragAnswer={result.rag_answer}
              noRagAnswer={result.no_rag_answer}
            />

            <SourcePanel sources={result.sources} />

            <ComparisonTable
              ragAnswer={result.rag_answer}
              noRagAnswer={result.no_rag_answer}
              mlPrediction={result.ml_prediction}
              llmPrediction={result.llm_prediction}
            />
          </>
        )}
      </main>

      <footer className="max-w-7xl mx-auto px-6 py-8 text-center text-xs text-slate-500">
        Twitter Customer Support ·{' '}
        <a className="underline hover:text-slate-700" href="/docs" target="_blank" rel="noreferrer">
          API docs
        </a>
      </footer>
    </div>
  );
}

function PrioritySummary({ mlLabel, mlConf, llmLabel, llmConf }) {
  const isUrgent = mlLabel === 'urgent' || llmLabel === 'urgent';
  const bg = isUrgent ? 'bg-red-50 border-red-200' : 'bg-emerald-50 border-emerald-200';
  const title = isUrgent ? '⚠ Flagged as urgent' : '✓ Classified as normal';
  const titleColor = isUrgent ? 'text-red-800' : 'text-emerald-800';

  return (
    <div className={`rounded-xl border p-4 ${bg}`}>
      <div className={`font-semibold mb-3 ${titleColor}`}>{title}</div>
      <div className="flex flex-wrap gap-4">
        <PredictionChip source="ML Model" label={mlLabel} conf={mlConf} note="calibrated" />
        <PredictionChip source="LLM" label={llmLabel} conf={llmConf} note="self-reported" />
      </div>
    </div>
  );
}

function PredictionChip({ source, label, conf, note }) {
  const urgent = label === 'urgent';
  const chip = urgent
    ? 'bg-red-100 text-red-700 border-red-200'
    : 'bg-slate-100 text-slate-600 border-slate-200';
  return (
    <div className={`flex items-center gap-2 border rounded-lg px-3 py-2 ${chip}`}>
      <span className="text-xs font-semibold mono">{source}</span>
      <span className="text-xs font-bold">{label}</span>
      <span className="text-xs opacity-70">{Math.round(conf * 100)}% ({note})</span>
    </div>
  );
}
