import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react'
import { api } from './api.js'
import Icon, { Logo } from './components/Icon.jsx'
import ImportSheet from './components/ImportSheet.jsx'
import { useLoad, useRoute } from './lib/hooks.js'
import { animate } from './lib/motion.js'
import About from './views/About.jsx'
import Audit from './views/Audit.jsx'
import CaseWorkspace from './views/CaseWorkspace.jsx'
import Export from './views/Export.jsx'
import NewCase from './views/NewCase.jsx'
import Pipeline from './views/Pipeline.jsx'
import Results from './views/Results.jsx'
import ReviewQueue from './views/ReviewQueue.jsx'

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
  ['pipeline', '#/pipeline', 'Pipeline'],
  ['queue', '#/queue', 'Review'],
  ['audit', '#/audit', 'Audit'],
  ['results', '#/results', 'Results'],
  ['about', '#/about', 'About'],
]
const TITLES = { pipeline: 'Pipeline', queue: 'Review', audit: 'Audit', export: 'Export', results: 'Results', about: 'About', new: 'New case' }

export default function App() {
  const route = useRoute()
  const [theme, nextTheme] = useTheme()
  const workspace = useLoad(() => api.workspace(), [])
  const queue = useLoad(() => api.queue(), [])
  const [importing, setImporting] = useState(false)
  const [arrivals, setArrivals] = useState(null)
  const [toast, setToast] = useState(null)
  const [menu, setMenu] = useState(false)
  const refresh = useCallback(() => { workspace.reload(); queue.reload() }, [workspace.reload, queue.reload]) // eslint-disable-line react-hooks/exhaustive-deps
  const current = route.page === 'case' || route.page === 'new' ? 'pipeline' : route.page === 'export' ? 'audit' : route.page
  const openItems = queue.data?.items.length || 0

  useEffect(() => {
    document.title = route.page === 'case' ? `${route.id} · ReSauce` : `${TITLES[route.page] || 'Pipeline'} · ReSauce`
  }, [route])

  const imported = useCallback((ids, message) => {
    setArrivals(new Set(ids))
    refresh()
    if (message) setToast({ text: message, key: Date.now() })
    if (route.page !== 'pipeline') window.location.hash = '#/pipeline'
  }, [refresh, route.page])

  // Orient: the indicator under the navigation travels to the page you chose instead of jumping.
  const navRef = useRef(null)
  const inkRef = useRef(null)
  const firstInk = useRef(true)
  useLayoutEffect(() => {
    const link = navRef.current?.querySelector('[aria-current="page"]')
    const ink = inkRef.current
    if (!ink) return
    if (!link) { ink.style.opacity = '0'; return }
    if (firstInk.current) ink.style.transition = 'none'
    ink.style.opacity = '1'
    ink.style.transform = `translateX(${link.offsetLeft}px) scaleX(${link.offsetWidth})`
    if (firstInk.current) { firstInk.current = false; requestAnimationFrame(() => { ink.style.transition = '' }) }
  }, [current])

  return (
    <div className="app">
      <a className="skip" href="#main">Skip to content</a>
      <div className="chrome">
      <header className="topbar on-dark">
        <a className="brand" href="#/pipeline"><Logo size={28} /><span className="wordmark">ReSauce</span></a>
        <nav className="nav" aria-label="Main" ref={navRef}>
          {NAV.map(([page, href, label]) => (
            <a key={page} className="nav-link" href={href} aria-current={current === page ? 'page' : undefined}>
              {label}
              {page === 'queue' && openItems > 0 && <span className="nav-dot" role="img" aria-label="open findings to review" />}
            </a>
          ))}
          <span className="nav-ink" ref={inkRef} aria-hidden="true" />
        </nav>
        <div className="top-actions">
          <button type="button" className="btn btn-invert btn-sm" onClick={() => setImporting(true)}><Icon name="import" size={16} />Import data</button>
          <button type="button" className="icon-btn icon-btn-bar" onClick={nextTheme} aria-label={`Theme: ${theme}. Change theme`} title={`Theme: ${theme}`}><Icon name="theme" size={18} /></button>
          <button type="button" className="icon-btn icon-btn-bar menu-btn" onClick={() => setMenu(true)} aria-label="Open the menu"><Icon name="menu" size={20} /></button>
        </div>
      </header>
      <p className="synthetic" role="note"><Icon name="shield" size={13} />Synthetic data only. Do not load real patient records.</p>
      </div>

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
        ) : route.page === 'results' ? (
          <Results />
        ) : route.page === 'about' ? (
          <About />
        ) : (
          <Pipeline workspace={workspace.data} arrivals={arrivals} onArrived={() => setArrivals(null)} onChanged={refresh} onImport={() => setImporting(true)} />
        )}
      </main>

      {importing && <ImportSheet workspace={workspace.data} onClose={() => setImporting(false)} onImported={imported} />}
      {menu && <MobileMenu current={current} onClose={() => setMenu(false)} onImport={() => { setMenu(false); setImporting(true) }} />}
      {toast && <Toast key={toast.key} text={toast.text} onDone={() => setToast(null)} />}
    </div>
  )
}

/** Phones: the navigation as a full-screen sheet; links settle in one after another. */
function MobileMenu({ current, onClose, onImport }) {
  const ref = useRef(null)
  useLayoutEffect(() => {
    const el = ref.current
    el.showModal()
    animate(el, [{ opacity: 0 }, { opacity: 1 }], { dur: 'base', fill: 'none' })
    el.querySelectorAll('.menu-link').forEach((link, i) => animate(link, [{ opacity: 0, transform: 'translateY(14px)' }, { opacity: 1, transform: 'none' }], { dur: 'slow', delay: 40 + i * 40 }))
  }, [])
  useEffect(() => {
    const el = ref.current
    const onHash = () => onClose()
    window.addEventListener('hashchange', onHash)
    el.addEventListener('close', onClose)
    return () => { window.removeEventListener('hashchange', onHash); el.removeEventListener('close', onClose) }
  }, [onClose])
  return (
    <dialog className="menu on-dark" ref={ref} aria-label="Menu">
      <button type="button" className="icon-btn icon-btn-bar menu-close" onClick={() => ref.current.close()} aria-label="Close the menu"><Icon name="close" size={22} /></button>
      <nav aria-label="Main">
        {NAV.map(([page, href, label]) => <a key={page} className="menu-link" href={href} aria-current={current === page ? 'page' : undefined}>{label}</a>)}
      </nav>
      <button type="button" className="btn btn-invert btn-lg menu-link" onClick={onImport}><Icon name="import" size={18} />Import data</button>
    </dialog>
  )
}

/** A short confirmation at the bottom of the screen; it rises in, waits, and falls away. */
function Toast({ text, onDone }) {
  const ref = useRef(null)
  useLayoutEffect(() => {
    const el = ref.current
    animate(el, [{ opacity: 0, transform: 'translateY(120%)' }, { opacity: 1, transform: 'none' }], { dur: 'spring-ui', ease: 'spring-ui', fill: 'none' })
    const t = setTimeout(() => {
      const a = animate(el, [{ opacity: 1, transform: 'none' }, { opacity: 0, transform: 'translateY(120%)' }], { dur: 'base', fill: 'forwards' })
      if (a) a.finished.then(onDone, onDone); else onDone()
    }, 4200)
    return () => clearTimeout(t)
  }, []) // eslint-disable-line react-hooks/exhaustive-deps
  return <p className="toast" ref={ref} role="status">{text}</p>
}
