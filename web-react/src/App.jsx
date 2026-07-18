import { Component, lazy, Suspense, useEffect, useMemo, useState } from 'react';
import {
  Activity,
  AlertTriangle,
  ArrowDownToLine,
  Beaker,
  BookOpen,
  CheckCircle2,
  Database,
  ExternalLink,
  FileText,
  GitCommit,
  Radio,
  ShieldCheck,
  Sparkles,
  Timer,
  Waves,
} from 'lucide-react';

const BurstHero = lazy(() => import('./BurstHero.jsx'));

const warningRules = [
  {
    key: 'sample-size',
    label: 'Underpowered configuration sample',
    description: 'The configuration count is below the declared minimum sample-size gate.',
    pattern: /below minimum(?:_sample_size| sample size)|underpowered|too few|n_configurations/i,
    tone: 'caveat',
  },
  {
    key: 'background-window',
    label: 'Background or window limitation',
    description: 'The background model or fixed timing window constrains interpretation.',
    pattern: /background|window|truncat|drift/i,
    tone: 'caveat',
  },
  {
    key: 'model-fit',
    label: 'Model-fit caveat',
    description: 'A documented model-fitting condition affected this timing configuration.',
    pattern: /fit|converge|covariance|model/i,
    tone: 'caveat',
  },
  {
    key: 'failure',
    label: 'Validation failure',
    description: 'A zero-tolerance validation condition failed and requires attention.',
    pattern: /fatal|zero[- ]tolerance|validation fail|\berror\b/i,
    tone: 'failure',
  },
];

function parseResultJson(text) {
  return JSON.parse(text.replace(/:\s*NaN(?=\s*[,}])/g, ': null'));
}

function useJson(path) {
  const [state, setState] = useState({ data: null, error: null, loading: true });

  useEffect(() => {
    const controller = new AbortController();
    fetch(path, { signal: controller.signal })
      .then((response) => {
        if (!response.ok) throw new Error(`${path}: HTTP ${response.status}`);
        return response.text();
      })
      .then((text) => setState({ data: parseResultJson(text), error: null, loading: false }))
      .catch((error) => {
        if (error.name !== 'AbortError') setState({ data: null, error, loading: false });
      });
    return () => controller.abort();
  }, [path]);

  return state;
}

function formatMetric(value) {
  return typeof value === 'number' && Number.isFinite(value) ? value.toPrecision(4) : 'Unavailable';
}

function SignalHeading({ channel, title, copy }) {
  return (
    <div className="signal-heading">
      <div><span>CH {channel}</span><i /></div>
      <h2>{title}</h2>
      {copy && <p>{copy}</p>}
    </div>
  );
}

function MetricCell({ metric, index }) {
  const available = typeof metric.estimate === 'number' && Number.isFinite(metric.estimate);
  const hasInterval = metric.uncertainty_low != null && metric.uncertainty_high != null;

  return (
    <article className={`metric-cell ${available ? '' : 'metric-missing'}`}>
      <div className="metric-channel">0{index + 1}</div>
      <p>{metric.name.replace(/_/g, ' ')}</p>
      <strong>{formatMetric(metric.estimate)}</strong>
      {available && <span>{metric.units}</span>}
      {hasInterval && <small>95% CI [{metric.uncertainty_low.toPrecision(3)}, {metric.uncertainty_high.toPrecision(3)}]</small>}
      {!hasInterval && <small>95% CI unavailable</small>}
      <small>sample size / {metric.sample_size}</small>
    </article>
  );
}

function groupWarnings(entries) {
  const groups = new Map();
  entries.forEach((entry, index) => {
    const text = String(entry);
    const rule = warningRules.find(({ pattern }) => pattern.test(text)) ?? {
      key: 'other',
      label: 'Other documented caveat',
      description: 'Additional timing-pipeline context retained for reproducibility.',
      tone: 'caveat',
    };
    const group = groups.get(rule.key) ?? { ...rule, entries: [] };
    group.entries.push({ text, index });
    groups.set(rule.key, group);
  });
  return [...groups.values()];
}

function WarningConsole({ warnings }) {
  const entries = useMemo(() => (Array.isArray(warnings.data) ? warnings.data : []), [warnings.data]);
  const groups = useMemo(() => groupWarnings(entries), [entries]);

  if (warnings.loading) return <p className="console-loading">Polling results/warnings.json…</p>;
  if (warnings.error) return <p className="console-error">Warning feed unavailable: {String(warnings.error)}</p>;
  if (entries.length === 0) {
    return <div className="console-clear"><CheckCircle2 size={20} />No warnings recorded in results/warnings.json.</div>;
  }

  return (
    <div>
      <div className="warning-readout">
        <div><strong>{entries.length}</strong><span>documented {entries.length === 1 ? 'entry' : 'entries'}</span></div>
        <p>Grouped by scientific meaning for rapid review. Every source string remains available in the raw feed below.</p>
      </div>
      <div className="warning-groups">
        {groups.map((group) => (
          <article className={`warning-group warning-${group.tone}`} key={group.key}>
            <span>{group.entries.length}</span>
            <div><h3>{group.label}</h3><p>{group.description}</p></div>
          </article>
        ))}
      </div>
      <details className="raw-console">
        <summary>Expand all {entries.length} raw {entries.length === 1 ? 'entry' : 'entries'}</summary>
        <ol>{entries.map((entry, index) => <li key={`${index}-${String(entry)}`}>{String(entry)}</li>)}</ol>
      </details>
    </div>
  );
}

function DataPanel({ icon: Icon, title, children, className = '' }) {
  return (
    <article className={`data-panel ${className}`}>
      <div className="data-title"><Icon size={17} aria-hidden="true" /><h3>{title}</h3></div>
      {children}
    </article>
  );
}

class HeroBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { failed: false };
  }

  static getDerivedStateFromError() {
    return { failed: true };
  }

  render() {
    if (this.state.failed) return <div className="burst-fallback">Burst schematic unavailable.</div>;
    return this.props.children;
  }
}

export default function App() {
  const project = useJson('./project.json');
  const summary = useJson('./results/summary.json');
  const warnings = useJson('./results/warnings.json');
  const benchmarks = useJson('./results/benchmarks.json');

  if (project.loading) return <main className="loading-screen">Acquiring trigger metadata…</main>;
  if (project.error || !project.data) {
    return <main className="loading-screen loading-error">Could not load project.json: {String(project.error)}</main>;
  }

  const p = project.data;
  const isDemo = summary.data?.data_kind === 'synthetic_smoke_test' || summary.data?.data_kind === 'synthetic_demo';

  return (
    <main className="burst-shell">
      <div className="scanline" aria-hidden="true" />
      <header className="telemetry-bar">
        <a href="#top"><Radio size={17} />GBM / T90</a>
        <div><span>Trigger timing laboratory</span><i /><span>{p.status}</span><i /><span>Priority {p.priority}/10</span></div>
        <p><span /> live assets</p>
      </header>

      <section className="burst-hero" id="top">
        <div className="hero-orbit-copy">
          <p><Sparkles size={14} /> {p.category}</p>
          <h1>{p.title}</h1>
        </div>
        <figure className="burst-figure">
          <HeroBoundary>
            <Suspense fallback={<div className="burst-fallback">Rendering high-energy schematic…</div>}>
              <BurstHero />
            </Suspense>
          </HeroBoundary>
          <figcaption>Stylized illustration, not flight data</figcaption>
        </figure>
        <div className="hero-question">
          <span>Research question / 10</span>
          <p>{p.question}</p>
          <div><b>{isDemo ? 'Synthetic demo' : 'Real public data'}</b><b>{p.dataMode}</b></div>
        </div>
        <nav className="hero-nav" aria-label="Report channels">
          <a href="#metrics">Metrics</a><a href="#figures">Figures</a><a href="#audit">Audit</a><a href="#method">Method</a><a href="#downloads">Data</a>
        </nav>
      </section>

      {isDemo && (
        <div className="demo-alert"><AlertTriangle size={18} /><p>Displayed output is a synthetic timing validation run, not real Fermi GBM telemetry.</p></div>
      )}

      <section className="signal-section metric-section" id="metrics">
        <SignalHeading channel="01" title="Duration estimates across the configuration grid" copy="Six headline values loaded directly from results/summary.json. Unavailable estimates remain explicit rather than coercing to zero." />
        {summary.error && <p className="console-error">Result feed unavailable: {String(summary.error)}</p>}
        <div className="metric-tape">
          {summary.data?.metrics?.slice(0, 6).map((metric, index) => <MetricCell metric={metric} index={index} key={metric.name} />)}
          {!summary.loading && !summary.data && !summary.error && <article className="metric-cell metric-missing"><p>No results yet</p><strong>Unavailable</strong><small>Run scripts/run_analysis.py</small></article>}
        </div>
      </section>

      <section className="signal-section figure-section" id="figures">
        <SignalHeading channel="02" title="Five traces through the burst-timing pipeline" copy="The sequence follows raw counts, cumulative duration markers, adaptive binning, bootstrap uncertainty, and model sensitivity." />
        <div className="trace-stack">
          {p.figures.map((figure, index) => (
            <figure className="trace-row" key={figure.id}>
              <div className="trace-index"><span>TRACE</span><strong>{String(index + 1).padStart(2, '0')}</strong></div>
              <img src={`./figures/${figure.id}.svg`} alt={figure.label} loading="lazy" />
              <figcaption><span>{figure.label}</span><i>{figure.id}</i></figcaption>
            </figure>
          ))}
        </div>
      </section>

      <section className="signal-section audit-section" id="audit">
        <SignalHeading channel="03" title="Interpretation stays behind the validation gate" />
        <div className="audit-grid">
          <DataPanel icon={ShieldCheck} title="Provenance boundary" className="provenance-panel">
            <p className="panel-copy">{p.novelty}</p>
            <div className="hard-gate"><AlertTriangle size={17} />No result is public-ready until validation and provenance checks pass.</div>
            {summary.data?.provenance && (
              <dl className="provenance-list">
                <div><dt><GitCommit size={14} />Git commit</dt><dd>{summary.data.provenance.git_commit}</dd></div>
                <div><dt><FileText size={14} />Config SHA-256</dt><dd title={summary.data.provenance.config_sha256}>{summary.data.provenance.config_sha256 ?? 'n/a'}</dd></div>
                <div><dt><Beaker size={14} />Package</dt><dd>{summary.data.provenance.package_version}</dd></div>
              </dl>
            )}
          </DataPanel>
          <DataPanel icon={Activity} title="Validation contract">
            <ul className="validation-grid">{p.validationContract.map((item, index) => <li key={item}><span>0{index + 1}</span>{item}</li>)}</ul>
          </DataPanel>
        </div>

        <div className="warning-console">
          <div className="console-header"><AlertTriangle size={16} /><span>WARNINGS.JSON / LIVE FEED</span><i /></div>
          <WarningConsole warnings={warnings} />
        </div>
      </section>

      <section className="signal-section method-section" id="method">
        <SignalHeading channel="04" title="A reproducibility lab, not a catalogue pipeline" />
        <div className="method-layout">
          <article className="method-core">
            <Timer size={22} />
            <p>Methodology</p>
            <h3>From event times to T5, T95, and T90.</h3>
            <span>{p.methodology}</span>
          </article>
          <div className="boundary-notes">
            <DataPanel icon={BookOpen} title="Assumptions">
              <ol>{p.assumptions.map((item, index) => <li key={item}><span>A{index + 1}</span>{item}</li>)}</ol>
            </DataPanel>
            <DataPanel icon={AlertTriangle} title="Limitations">
              <ol>{p.limitations.map((item, index) => <li key={item}><span>L{index + 1}</span>{item}</li>)}</ol>
            </DataPanel>
          </div>
        </div>
      </section>

      <section className="signal-section download-section" id="downloads">
        <SignalHeading channel="05" title="Export the timing evidence" copy="Machine-readable results and the archive checksum manifest used to restore the real TTE inputs." />
        <div className="download-layout">
          <div className="download-console">
            <a href="./manifest.csv" download><span>FILE 01</span><strong>data/manifest.csv</strong><ArrowDownToLine size={17} /></a>
            <a href="./results/summary.json" download><span>FILE 02</span><strong>results/summary.json</strong><ArrowDownToLine size={17} /></a>
            {benchmarks.data && <a href="./results/benchmarks.json" download><span>FILE 03</span><strong>results/benchmarks.json</strong><ArrowDownToLine size={17} /></a>}
          </div>
          <DataPanel icon={Database} title="Citation and licence" className="citation-panel">
            <p>Author <strong>{p.citation.author}</strong></p>
            <p>Licence <strong>{p.citation.license}</strong></p>
            <a href={p.citation.repository}>Repository <ExternalLink size={14} /></a>
          </DataPanel>
        </div>
      </section>

      <footer className="burst-footer"><span><Waves size={15} /> Fermi GBM T90 reproducibility lab</span><span>Biswajit Jana / 2026</span></footer>
    </main>
  );
}
