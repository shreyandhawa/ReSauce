import { useCallback, useEffect, useState } from 'react'
import { api } from './api.js'
import Icon from './components/Icon.jsx'
import { useLoad, useRoute } from './lib/hooks.js'
import About from './views/About.jsx'
import Audit from './views/Audit.jsx'
import CaseWorkspace from './views/CaseWorkspace.jsx'
import Cases from './views/Cases.jsx'
import Export from './views/Export.jsx'
import NewCase from './views/NewCase.jsx'
import ReviewQueue from './views/ReviewQueue.jsx'
import Validation from './views/Validation.jsx'

const THEMES = ['system', 'light', 'dark']

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
  ['cases', '#/cases', 'Cases', 'cases'],
  ['queue', '#/queue', 'Review queue', 'queue'],
  ['audit', '#/audit', 'Audit trail', 'audit'],
  ['export', '#/export', 'Export', 'export'],
]
const SECONDARY = [
  ['validation', '#/validation', 'Validation', 'validation'],
  ['about', '#/about', 'About & limitations', 'about'],
]

export default function App() {
  const route = useRoute()
  const [theme, nextTheme] = useTheme()
  const workspace = useLoad(() => api.workspace(), [])
  const queue = useLoad(() => api.queue(), [])
  const refresh = useCallback(() => { workspace.reload(); queue.reload() }, [workspace.reload, queue.reload]) // eslint-disable-line react-hooks/exhaustive-deps
  const current = route.page === 'case' || route.page === 'new' ? 'cases' : route.page
  const counts = { cases: workspace.data?.case_count, queue: queue.data?.items.length }

  useEffect(() => {
    document.title = { case: `${route.id} · ReSauce`, new: 'New case · ReSauce' }[route.page] || `${[...NAV, ...SECONDARY].find(([p]) => p === current)?.[2] || 'Cases'} · ReSauce`
  }, [route, current])

  const link = ([page, href, label, icon]) => (
    <a key={page} className="nav-link" href={href} aria-current={current === page ? 'page' : undefined}>
      <Icon name={icon} size={18} />{label}
      {counts[page] != null && <span className="count" aria-label={`${counts[page]}${page === 'queue' ? ' open findings' : ' cases'}`}>{counts[page]}</span>}
    </a>
  )

  return (
    <div className="shell">
      <a className="skip" href="#main">Skip to content</a>
      <nav className="sidebar" aria-label="Main">
        <a className="brand" href="#/cases">ReSauce</a>
        {NAV.map(link)}
        <div className="nav-gap" />
        <div className="nav-sub">Reference</div>
        {SECONDARY.map(link)}
        <div className="sidebar-foot">
          <span>Workspace<br /><span className="mono">{workspace.data?.path || '…'}</span></span>
          {workspace.data?.pipeline && (
            <span>Pipeline <span className="mono">{workspace.data.pipeline.tag}</span>{workspace.data.pipeline.frozen_files_match ? '' : ' (frozen files changed)'}</span>
          )}
          <button type="button" className="theme-btn" onClick={nextTheme} aria-label={`Theme: ${theme}. Change theme`}>Theme: {theme}</button>
        </div>
      </nav>
      <div className="main">
        <p className="banner" role="note"><Icon name="shield" size={14} />Synthetic data only. Do not load real patient records.</p>
        <main id="main" tabIndex={-1}>
          {workspace.error ? (
            <div className="page"><p className="callout callout-alert">The ReSauce server could not be reached ({workspace.error.message}). Start it with <span className="mono">python -m app</span> and reload this page.</p></div>
          ) : route.page === 'case' ? (
            <CaseWorkspace key={route.id} caseId={route.id} onChanged={refresh} />
          ) : route.page === 'new' ? (
            <NewCase onChanged={refresh} />
          ) : route.page === 'queue' ? (
            <ReviewQueue key={route.params.case || 'all'} caseFilter={route.params.case} onChanged={refresh} />
          ) : route.page === 'audit' ? (
            <Audit />
          ) : route.page === 'export' ? (
            <Export />
          ) : route.page === 'validation' ? (
            <Validation />
          ) : route.page === 'about' ? (
            <About />
          ) : (
            <Cases workspace={workspace.data} onChanged={refresh} />
          )}
        </main>
      </div>
    </div>
  )
}
