import { useCallback, useEffect, useRef, useState } from 'react'
import { flushSync } from 'react-dom'
import { hasOrigin, reducedMotion } from './motion.js'

/** Load a promise-returning call; returns { data, error, loading, reload }. */
export function useLoad(load, deps) {
  const [state, setState] = useState({ data: null, error: null, loading: true })
  const [tick, setTick] = useState(0)
  useEffect(() => {
    let live = true
    setState((s) => ({ ...s, loading: true, error: null }))
    load()
      .then((data) => live && setState({ data, error: null, loading: false }))
      .catch((error) => live && setState({ data: null, error, loading: false }))
    return () => { live = false }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick])
  const reload = useCallback(() => setTick((t) => t + 1), [])
  return { ...state, reload }
}

const PAGES = ['pipeline', 'new', 'case', 'queue', 'audit', 'export', 'results', 'about']
const OLD_NAMES = { cases: 'pipeline', validation: 'results' } // links from before the redesign keep working

function readRoute() {
  const [path, query = ''] = window.location.hash.replace(/^#\/?/, '').split('?')
  const [raw, id] = path.split('/')
  const page = OLD_NAMES[raw] || raw
  const params = Object.fromEntries(new URLSearchParams(query))
  if (page === 'case' && id) return { page, id: decodeURIComponent(id), params, key: `case/${id}` }
  if (PAGES.includes(page) && page !== 'case') return { page, params, key: page }
  return { page: 'pipeline', params, key: 'pipeline' }
}

/** Whether a media query matches, kept up to date. */
export function useMedia(query) {
  const [matches, setMatches] = useState(() => window.matchMedia(query).matches)
  useEffect(() => {
    const mq = window.matchMedia(query)
    const on = () => setMatches(mq.matches)
    on()
    mq.addEventListener('change', on)
    return () => mq.removeEventListener('change', on)
  }, [query])
  return matches
}

/**
 * The current hash route. Orient: a route change cross-fades the page area (View Transitions),
 * except when opening a case from a row, which expands from that row instead (CaseWorkspace).
 * Each page's scroll position is kept, so going back to the list returns to the same place.
 */
export function useRoute() {
  const [route, setRoute] = useState(readRoute)
  const scrolls = useRef({})
  const current = useRef(route)
  useEffect(() => {
    const on = () => {
      scrolls.current[current.current.key] = window.scrollY
      const next = readRoute()
      current.current = next
      const apply = () => flushSync(() => setRoute(next))
      const expanding = next.page === 'case' && hasOrigin()
      if (document.startViewTransition && !reducedMotion() && !expanding && document.visibilityState === 'visible') {
        const t = document.startViewTransition(apply)
        t.ready.catch(() => {}) // skipped transitions (e.g. the tab was hidden) still apply the change
        t.finished.catch(() => {})
      } else apply()
      requestAnimationFrame(() => window.scrollTo(0, scrolls.current[next.key] || 0))
    }
    window.addEventListener('hashchange', on)
    return () => window.removeEventListener('hashchange', on)
  }, [])
  return route
}

/** Session-scoped value (the reviewer's name is asked once per session). */
export function useSessionValue(key) {
  const [value, setValue] = useState(() => { try { return sessionStorage.getItem(key) || '' } catch { return '' } })
  const save = useCallback((v) => {
    setValue(v)
    try { sessionStorage.setItem(key, v) } catch { /* storage blocked: kept for this page only */ }
  }, [key])
  return [value, save]
}
