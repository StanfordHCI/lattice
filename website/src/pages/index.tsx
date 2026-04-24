import type {ReactNode} from 'react';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';

import styles from './index.module.css';

/* ─── Hero ───────────────────────────────────────────────────────── */
function Hero() {
  const {siteConfig} = useDocusaurusContext();
 
  return (
    <header className={styles.heroBanner}>
      <div className={`container ${styles.heroInner}`}>
        <div className={styles.heroContent}>
          <Heading as="h1" className={styles.heroTitle}>
            Behavior Latticing
          </Heading>
          <p className={styles.heroSubtitle}>
            Transform unstructured interaction traces into inferences about user motivations.
          </p>
          <div className={styles.buttons}>
            <Link className={styles.btnPrimary} to="/docs/guides/quickstart">
              Get started →
            </Link>
            <Link className={styles.btnSecondary} to="/docs/intro">
              What is Behavior Latticing?
            </Link>
          </div>
        </div>
        <div className={styles.heroDemo}>
          <iframe
            src={`${siteConfig.baseUrl}hero_lattice.html`}
            title="Behavior Lattice interactive demo"
            className={styles.heroDemoFrame}
            scrolling="no"
          />
        </div>
      </div>
    </header>
  );
}

/* ─── Code preview ───────────────────────────────────────────────── */
function CodePreview() {
  return (
    <div className={styles.codeStrip}>
      <div className={styles.codeStripInner}>
        <p className={styles.codeStripLabel}>Quick look</p>
        <div className={styles.codeBlock}>
          <div className={styles.codeBlockHeader}>
            <span className={`${styles.dot} ${styles.dotRed}`} />
            <span className={`${styles.dot} ${styles.dotYellow}`} />
            <span className={`${styles.dot} ${styles.dotGreen}`} />
            <span className={styles.codeBlockFilename}>example.py</span>
          </div>
          <div className={styles.codeBlockBody}>
            <pre>
{`<span class="${styles.cKeyword}">from</span> lattice <span class="${styles.cKeyword}">import</span> Lattice, AsyncLLM, SyncLLM
<span class="${styles.cKeyword}">import</span> os

<span class="${styles.cComment}"># 1. Create the lattice with your data and models</span>
<span class="${styles.cParam}">l</span> = <span class="${styles.cFn}">Lattice</span>(
    <span class="${styles.cParam}">name</span>=<span class="${styles.cString}">"Alice"</span>,
    <span class="${styles.cParam}">interactions</span>=interaction_traces,
    <span class="${styles.cParam}">description</span>=<span class="${styles.cString}">"the user's ChatGPT conversations"</span>,
    <span class="${styles.cParam}">model</span>=<span class="${styles.cFn}">AsyncLLM</span>(<span class="${styles.cParam}">name</span>=<span class="${styles.cString}">"claude-sonnet-4-6"</span>, <span class="${styles.cParam}">api_key</span>=os.<span class="${styles.cFn}">getenv</span>(<span class="${styles.cString}">"ANTHROPIC_API_KEY"</span>)),
    <span class="${styles.cParam}">evidence_model</span>=<span class="${styles.cFn}">AsyncLLM</span>(<span class="${styles.cParam}">name</span>=<span class="${styles.cString}">"claude-sonnet-4-6"</span>, <span class="${styles.cParam}">api_key</span>=os.<span class="${styles.cFn}">getenv</span>(<span class="${styles.cString}">"ANTHROPIC_API_KEY"</span>)),
    <span class="${styles.cParam}">format_model</span>=<span class="${styles.cFn}">SyncLLM</span>(<span class="${styles.cParam}">name</span>=<span class="${styles.cString}">"claude-sonnet-4-6"</span>, <span class="${styles.cParam}">api_key</span>=os.<span class="${styles.cFn}">getenv</span>(<span class="${styles.cString}">"ANTHROPIC_API_KEY"</span>)),
)

<span class="${styles.cComment}"># 2. Define layers: each session → L1, every 10 sessions → L2</span>
<span class="${styles.cParam}">config</span> = {
    <span class="${styles.cString}">0</span>: {<span class="${styles.cString}">"type"</span>: <span class="${styles.cString}">"session"</span>, <span class="${styles.cString}">"value"</span>: <span class="${styles.cString}">"1"</span>},
    <span class="${styles.cString}">1</span>: {<span class="${styles.cString}">"type"</span>: <span class="${styles.cString}">"session"</span>, <span class="${styles.cString}">"value"</span>: <span class="${styles.cString}">"10"</span>},
}

<span class="${styles.cComment}"># 3. Build, save, visualize</span>
<span class="${styles.cKeyword}">await</span> l.<span class="${styles.cFn}">build</span>(config)
l.<span class="${styles.cFn}">save</span>(<span class="${styles.cString}">"lattice.json"</span>)
l.<span class="${styles.cFn}">visualize</span>().<span class="${styles.cFn}">show</span>()`}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
}

/* ─── How it works ───────────────────────────────────────────────── */
const steps = [
  {
    n: '01',
    title: 'Observe',
    desc: 'The Observer reads windows of raw interactions and prompts an LLM to infer what the user thinks and feels — grounded in named behavioral evidence.',
  },
  {
    n: '02',
    title: 'Synthesize',
    desc: 'Observations are grouped by session and synthesized into insights with context on when each pattern applies.',
  },
  {
    n: '03',
    title: 'Layer',
    desc: 'Insights from multiple sessions are recursively merged into higher-order patterns',
  },
  {
    n: '04',
    title: 'Explore',
    desc: 'Navigate the resulting lattice interactively — click any node to read its full text and trace it back to its supporting observations.',
  },
];

function HowItWorks() {
  return (
    <section className={styles.stepsSection}>
      <div className="container">
        <p className={styles.sectionLabel}>How it works</p>
        <Heading as="h2" className={styles.sectionHeading}>
          From raw data to inferred motivations
        </Heading>
        <div className={styles.steps}>
          {steps.map(s => (
            <div key={s.n} className={styles.step}>
              {s.n}
              <h3 className={styles.stepTitle}>{s.title}</h3>
              <p className={styles.stepDesc}>{s.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* ─── Features ───────────────────────────────────────────────────── */
function Features() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <section className={styles.featuresSection}>
      <div className="container">
        <p className={styles.sectionLabel}>Explore</p>
        <Heading as="h2" className={styles.sectionHeading}>
          See Behavior Latticing in action
        </Heading>
        <div className={styles.latticeEmbed}>
          <iframe
            src={`${siteConfig.baseUrl}demo.html`}
            title="Behavior Lattice demo"
            className={styles.latticeFrame}
            scrolling="no"
          />
        </div>
      </div>
    </section>
  );
}

/* ─── Page ───────────────────────────────────────────────────────── */
export default function Home(): ReactNode {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout title={siteConfig.title} description={siteConfig.tagline}>
      <Hero />
      <main>
        {/* <CodePreview /> */}
        <HowItWorks />
        <Features />
      </main>
    </Layout>
  );
}
