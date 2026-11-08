import { useEffect, useState } from 'react'
import { api } from './api.js'
import { useLoad, useRoute } from './lib/hooks.js'
import Overview from './views/Overview.jsx'
import Cases from './views/Cases.jsx'
import Investigate from './views/Investigate.jsx'
import Methods from './views/Methods.jsx'
import { Problem } from './components/Bits.jsx'

const THEMES = ['system', 'light', 'dark']
const THEME_LABEL = { system: 'Theme: system', light: 'Theme: light', dark: 'Theme: dark' }

function useTheme() {
  const [theme, setTheme] = useState(() => document.documentElement.dataset.theme || 'system')
  useEffect(() => {
    if (theme === 'system') delete document.documentElement.dataset.theme
    else document.documentElement.dataset.theme = theme
    try {
      if (theme === 'system') localStorage.removeItem('resauce-theme')
      else localStorage.setItem('resauce-theme', theme)
    } catch { /* storage blocked: the choice lasts for this visit only */ }
  }, [theme])
  return [theme, () => setTheme(THEMES[(THEMES.indexOf(theme) + 1) % THEMES.length])]
}

const NAV = [
  ['overview', '#/', 'Results'],
  ['cases', '#/cases', 'Cases'],
  ['methods', '#/methods', 'Methods & limitations'],
]

export default function App() {
  const route = useRoute()
  const [theme, nextTheme] = useTheme()
  const summary = useLoad(() => api.summary(), [])
  const current = route.page === 'case' ? 'cases' : route.page

  return (
    <>
      <a className="skip" href="#main">Skip to content</a>
      <header className="masthead">
        <div className="masthead-inner">
          <a className="wordmark" href="#/">ReSauce</a>
          <nav aria-label="Main">
            {NAV.map(([page, href, label]) => (
              <a key={page} href={href} aria-current={current === page ? 'page' : undefined}>{label}</a>
            ))}
          </nav>
          <button type="button" className="theme" onClick={nextTheme} aria-label={`${THEME_LABEL[theme]}. Change theme`}>
            {THEME_LABEL[theme]}
          </button>
        </div>
      </header>

      <main id="main" tabIndex={-1}>
        {summary.error ? (
          <Problem title="The results could not be loaded" error={summary.error} />
        ) : route.page === 'cases' ? (
          <Cases />
        ) : route.page === 'case' ? (
          <Investigate key={route.id} caseId={route.id} summary={summary.data} />
        ) : route.page === 'methods' ? (
          <Methods summary={summary.data} />
        ) : (
          <Overview summary={summary.data} />
        )}
      </main>

      <footer className="colophon">
        <div className="colophon-inner">
          <p><strong>Synthetic data only.</strong> Results on synthetic data are not clinical validation. ReSauce is a research proof of concept, not a clinical decision tool.</p>
          {summary.data && <p>Reference answers: {summary.data.reference_label}.</p>}
        </div>
      </footer>
    </>
  )
}
