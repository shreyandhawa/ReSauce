import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import { api } from '../api.js'
import Icon from './Icon.jsx'
import { animate } from '../lib/motion.js'

/**
 * Import data: the beginning of the pipeline. Offers exactly what the server supports: the
 * synthetic example set, a folder inside this project (the server only accepts a path there, so
 * files cannot be dropped in), or a case typed into the form. Imported cases enter the stage.
 */
export default function ImportSheet({ workspace, onClose, onImported }) {
  const ref = useRef(null)
  const closing = useRef(false)
  const [examples, setExamples] = useState({})
  const [folder, setFolder] = useState({ path: '' })

  // Orient: the sheet materialises in place (scale, blur and opacity together); the page dims behind it.
  useLayoutEffect(() => {
    const el = ref.current
    el.showModal()
    animate(el, [{ opacity: 0, transform: 'translateY(12px) scale(0.97)', filter: 'blur(10px)' }, { opacity: 1, transform: 'none', filter: 'blur(0px)' }], { dur: 'spring-sheet', ease: 'spring-sheet', fill: 'none' })
  }, [])

  const close = (after) => {
    if (closing.current) return
    closing.current = true
    const el = ref.current
    const a = animate(el, [{ opacity: 1, transform: 'none' }, { opacity: 0, transform: 'translateY(8px) scale(0.98)' }], { dur: 'fast', ease: 'out', fill: 'forwards' })
    const done = () => { el.close(); onClose(); after?.() }
    if (a) a.finished.then(done, done); else done()
  }

  useEffect(() => {
    const el = ref.current
    const onCancel = (e) => { e.preventDefault(); close() }
    el.addEventListener('cancel', onCancel)
    return () => el.removeEventListener('cancel', onCancel)
  })

  const importExamples = async () => {
    setExamples({ busy: true })
    try {
      const r = await api.loadExamples()
      if (r.copied.length) { close(() => onImported(r.copied, `${r.copied.length} example cases imported from ${r.source}.`)); return }
      setExamples({ note: `All ${r.skipped_existing.length} example cases are already in the workspace.` })
    } catch (error) { setExamples({ error: error.message }) }
  }

  const importFolder = async (e) => {
    e.preventDefault()
    setFolder((f) => ({ path: f.path, busy: true }))
    try {
      const r = await api.importFolder(folder.path)
      if (r.imported.length && !r.invalid.length) {
        close(() => onImported(r.imported, `${r.imported.length} case${r.imported.length === 1 ? '' : 's'} imported from ${r.source}.${r.skipped_existing.length ? ` ${r.skipped_existing.length} already there.` : ''}`))
        return
      }
      setFolder({ path: folder.path, result: r })
      if (r.imported.length) onImported(r.imported, null)
    } catch (error) { setFolder({ path: folder.path, error: error.message }) }
  }

  return (
    <dialog className="import" ref={ref} aria-labelledby="imp-title" onClick={(e) => { if (e.target === ref.current) close() }}>
      <div className="import-inner">
        <header className="import-head">
          <h2 id="imp-title">Import data</h2>
          <p>Cases enter the pipeline on the left of the stage. Everything is copied into the workspace <span className="mono">{workspace?.path}</span>; the source is only read.</p>
          <button type="button" className="icon-btn import-close" onClick={() => close()} aria-label="Close"><Icon name="close" size={18} /></button>
        </header>

        <ol className="import-options">
          <li className="import-opt">
            <div className="import-text">
              <h3>Synthetic example set</h3>
              <p>{workspace?.example_count ?? 'The'} fictional cases from <span className="mono">data/dev-v1</span>. The originals are never changed.</p>
              {examples.note && <p className="import-note" role="status">{examples.note}</p>}
              {examples.error && <p className="problem-text problem-in" role="alert"><Icon name="error" size={14} />{examples.error}</p>}
            </div>
            <button type="button" className="btn btn-primary" onClick={importExamples} disabled={examples.busy}>{examples.busy ? 'Copying…' : 'Import examples'}</button>
          </li>

          <li className="import-opt">
            <form className="import-text" onSubmit={importFolder}>
              <h3><label htmlFor="imp-path">A folder in this project</label></h3>
              <p id="imp-hint">A dataset folder (with <span className="mono">cases/</span>) or one case folder. In this proof of concept only folders inside the ReSauce folder can be opened, so type its path; files cannot be dropped here.</p>
              <div className="import-row">
                <input id="imp-path" className="input mono" value={folder.path} aria-describedby="imp-hint" placeholder="data/dev-v1"
                  onChange={(e) => setFolder({ path: e.target.value })} aria-invalid={folder.error ? true : undefined} />
                <button type="submit" className="btn" disabled={folder.busy || !folder.path.trim()}>{folder.busy ? 'Checking…' : 'Import folder'}</button>
              </div>
              {folder.error && <p className="problem-text problem-in" role="alert"><Icon name="error" size={14} />{folder.error}</p>}
              {folder.result && <FolderResult r={folder.result} />}
            </form>
          </li>

          <li className="import-opt">
            <div className="import-text">
              <h3>Enter a case by hand</h3>
              <p>Type or paste the notes and the research record. Saving checks the case with the same loader the pipeline uses.</p>
            </div>
            <a className="btn" href="#/new" onClick={(e) => { e.preventDefault(); close(() => { window.location.hash = '#/new' }) }}>Open the form</a>
          </li>
        </ol>

        <p className="import-foot"><Icon name="shield" size={15} />Synthetic data only. Do not import real patient records.</p>
      </div>
    </dialog>
  )
}

function FolderResult({ r }) {
  return (
    <div className="import-result" role="status">
      <p><strong>{r.imported.length ? `Imported ${r.imported.length}` : 'Nothing imported'}</strong> from <span className="mono">{r.source}</span>{r.skipped_existing.length ? `; ${r.skipped_existing.length} already in the workspace` : ''}.</p>
      {r.invalid.length > 0 && (
        <>
          <p className="problem-text"><Icon name="error" size={14} />{r.invalid.length} did not pass the data-format check and were not imported:</p>
          <ul>{r.invalid.map((x) => <li key={x.case}><span className="mono">{x.case}</span>: {x.problems[0]}</li>)}</ul>
        </>
      )}
    </div>
  )
}
