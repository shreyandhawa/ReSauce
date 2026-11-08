import { useEffect, useState } from 'react'

/** Load a promise-returning call; returns { data, error, loading }. */
export function useLoad(load, deps) {
  const [state, setState] = useState({ data: null, error: null, loading: true })
  useEffect(() => {
    let live = true
    setState((s) => ({ ...s, loading: true, error: null }))
    load()
      .then((data) => live && setState({ data, error: null, loading: false }))
      .catch((error) => live && setState({ data: null, error, loading: false }))
    return () => { live = false }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps)
  return state
}

export function useReducedMotion() {
  const query = '(prefers-reduced-motion: reduce)'
  const [reduced, setReduced] = useState(() => window.matchMedia(query).matches)
  useEffect(() => {
    const m = window.matchMedia(query)
    const on = () => setReduced(m.matches)
    m.addEventListener('change', on)
    return () => m.removeEventListener('change', on)
  }, [])
  return reduced
}

/** Current hash route: { page: 'overview' | 'cases' | 'case' | 'methods', id? }. */
export function useRoute() {
  const read = () => {
    const h = window.location.hash.replace(/^#\/?/, '')
    const [page, id] = h.split('/')
    if (page === 'cases') return { page: 'cases' }
    if (page === 'case' && id) return { page: 'case', id: decodeURIComponent(id) }
    if (page === 'methods') return { page: 'methods' }
    return { page: 'overview' }
  }
  const [route, setRoute] = useState(read)
  useEffect(() => {
    const on = () => {
      setRoute(read())
      window.scrollTo(0, 0)
    }
    window.addEventListener('hashchange', on)
    return () => window.removeEventListener('hashchange', on)
  }, [])
  return route
}
