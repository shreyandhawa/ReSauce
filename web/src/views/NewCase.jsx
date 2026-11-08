import { cloneElement, useEffect, useRef, useState } from 'react'
import { api } from '../api.js'
import Icon from '../components/Icon.jsx'
import { NOTE_TYPES, ROLES } from '../lib/format.js'
import { reducedMotion } from '../lib/motion.js'

const blankVersion = () => ({ author_role: 'attending_physician', documented_at: '', status: 'signed', text: '', amendment_reason: '', loaded: '' })
const blankDoc = () => ({ note_type: 'physician_progress_note', versions: [blankVersion()] })
const blankRecord = () => ({ recorded_at: '', icans_reported: true, onset_date: '', max_grade: '', change_reason: '' })
const blank = () => ({ case_id: '', age_at_infusion: '', infusion_date: '', documents: [blankDoc()], record_versions: [blankRecord()] })

export default function NewCase({ onChanged }) {
  const [form, setForm] = useState(blank)
  const [problems, setProblems] = useState({})
  const [round, setRound] = useState(0) // re-keys problem messages so each save shows them afresh
  const [summary, setSummary] = useState(null)
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(null)
  const dialog = useRef(null)
  const formRef = useRef(null)

  const update = (fn) => setForm((f) => { const next = structuredClone(f); fn(next); return next })
  const p = (key) => problems[key]

  // Guide attention: after a failed save, bring the first problem into view and focus its field.
  useEffect(() => {
    if (!round || !Object.keys(problems).length) return
    const el = formRef.current?.querySelector('[data-problem] input, [data-problem] select, [data-problem] textarea')
    el?.scrollIntoView({ block: 'center', behavior: reducedMotion() ? 'auto' : 'smooth' })
    el?.focus({ preventScroll: true })
  }, [round, problems])

  const askSave = (e) => { e.preventDefault(); dialog.current?.showModal() }
  const save = async () => {
    dialog.current?.close()
    setSaving(true); setSummary(null)
    try {
      const body = { ...form, documents: form.documents.map((d) => ({ ...d, versions: d.versions.map(({ loaded, ...v }) => v) })) } // eslint-disable-line no-unused-vars
      const r = await api.createCase(body)
      setProblems({}); setSaved(r.case_id); onChanged?.()
    } catch (error) {
      const map = {}
      const general = []
      for (const pr of error.problems || []) {
        if (pr.key === 'form' || !document.querySelector(`[data-key="${CSS.escape(pr.key)}"]`)) general.push(pr.message)
        else map[pr.key] = map[pr.key] ? `${map[pr.key]}; ${pr.message}` : pr.message
      }
      setProblems(map)
      setSummary({ text: error.message, general })
      setRound((n) => n + 1)
    }
    setSaving(false)
  }

  const loadTxt = (di, vi) => async (e) => {
    const file = e.target.files?.[0]
    if (!file) return
    const raw = await file.text()
    const text = raw.replace(/\r\n?/g, '\n')
    update((f) => { const v = f.documents[di].versions[vi]; v.text = text; v.loaded = `Loaded ${file.name}${text !== raw ? ' (Windows line endings changed to \\n, as the data format requires)' : ''}.` })
    e.target.value = ''
  }

  if (saved) {
    return (
      <div className="page">
        <div className="page-head"><h1>New case</h1></div>
        {/* Connect cause and effect: the save is confirmed in place of the form's save bar. */}
        <div className="panel saved-in" role="status" style={{ display: 'grid', gap: 12, maxWidth: 640 }}>
          <span className="saved"><Icon name="reviewed" size={20} />Saved {saved} and validated with the data-format loader.</span>
          <p className="note">The case is in the workspace. Verify it to run the frozen pipeline.</p>
          <div style={{ display: 'flex', gap: 10 }}>
            <a className="btn btn-primary" href={`#/case/${encodeURIComponent(saved)}`}>Open {saved}</a>
            <button type="button" className="btn" onClick={() => { setForm(blank()); setSaved(null); setRound(0) }}>Enter another case</button>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="page">
      <div className="page-head">
        <div><h1>New case</h1><p className="sub">Enter a fictional case. Saving writes it in the ReSauce data format and checks it with the same loader the pipeline uses; any problem appears next to its field.</p></div>
      </div>
      <form className="form" ref={formRef} onSubmit={askSave} noValidate>
        <section className="form-section" aria-labelledby="nc-case">
          <h2 id="nc-case">Case details</h2>
          <div className="grid-3">
            <Field k="case.case_id" label="Pseudonymous case ID" hint="SYN- and 4 digits, e.g. SYN-0901" problem={p('case.case_id')} round={round}>
              <input className="input mono" value={form.case_id} onChange={(e) => update((f) => { f.case_id = e.target.value.toUpperCase() })} />
            </Field>
            <Field k="case.infusion_date" label="Infusion date (Day 0)" problem={p('case.infusion_date')} round={round}>
              <input className="input" type="date" value={form.infusion_date} onChange={(e) => update((f) => { f.infusion_date = e.target.value })} />
            </Field>
            <Field k="case.age_at_infusion" label="Age at infusion" hint="Whole years" problem={p('case.age_at_infusion')} round={round}>
              <input className="input" inputMode="numeric" value={form.age_at_infusion} onChange={(e) => update((f) => { f.age_at_infusion = e.target.value })} />
            </Field>
          </div>
        </section>

        <section className="form-section" aria-labelledby="nc-docs">
          <h2 id="nc-docs">Documents</h2>
          {form.documents.map((doc, di) => (
            <div key={di} className="doc-block">
              <div className="doc-block-head">
                <h3>Document D{String(di + 1).padStart(2, '0')}</h3>
                {form.documents.length > 1 && <button type="button" className="btn btn-quiet btn-sm" onClick={() => update((f) => { f.documents.splice(di, 1) })}>Remove document</button>}
              </div>
              <Field k={`doc.${di}.1.note_type`} label="Document type" problem={p(`doc.${di}.1.note_type`)} round={round}>
                <select className="select" value={doc.note_type} onChange={(e) => update((f) => { f.documents[di].note_type = e.target.value })}>
                  {Object.entries(NOTE_TYPES).map(([v, t]) => <option key={v} value={v}>{t}</option>)}
                </select>
              </Field>
              {doc.versions.map((v, vi) => {
                const n = vi + 1
                const key = (name) => `doc.${di}.${n}.${name}`
                return (
                  <div key={vi} className="version-block">
                    <div className="doc-block-head">
                      <h3>Version {n}</h3>
                      {vi > 0 && vi === doc.versions.length - 1 && <button type="button" className="btn btn-quiet btn-sm" onClick={() => update((f) => { f.documents[di].versions.pop() })}>Remove version</button>}
                    </div>
                    <div className="grid-3">
                      <Field k={key('documented_at')} label="Documented at" hint="Date and time the note was written" problem={p(key('documented_at'))} round={round}>
                        <input className="input" type="datetime-local" step="60" value={v.documented_at} onChange={(e) => update((f) => { f.documents[di].versions[vi].documented_at = e.target.value })} />
                      </Field>
                      <Field k={key('author_role')} label="Author role" hint="A role, never a name" problem={p(key('author_role'))} round={round}>
                        <select className="select" value={v.author_role} onChange={(e) => update((f) => { f.documents[di].versions[vi].author_role = e.target.value })}>
                          {Object.entries(ROLES).map(([r, t]) => <option key={r} value={r}>{t}</option>)}
                        </select>
                      </Field>
                      <Field k={key('status')} label="Status" problem={p(key('status'))} round={round}>
                        <select className="select" value={v.status} onChange={(e) => update((f) => { f.documents[di].versions[vi].status = e.target.value })}>
                          <option value="signed">signed</option><option value="unsigned">unsigned</option>
                        </select>
                      </Field>
                    </div>
                    {vi > 0 && (
                      <Field k={key('amendment_reason')} label="Amendment reason" problem={p(key('amendment_reason'))} round={round}>
                        <input className="input" value={v.amendment_reason} onChange={(e) => update((f) => { f.documents[di].versions[vi].amendment_reason = e.target.value })} />
                      </Field>
                    )}
                    <Field k={key('text')} label="Note text" hint="Paste the note, or load a .txt file. Event times stay in the text." problem={p(key('text'))} round={round}>
                      <textarea className="textarea" value={v.text} onChange={(e) => update((f) => { f.documents[di].versions[vi].text = e.target.value; f.documents[di].versions[vi].loaded = '' })} />
                      <span className="hint" style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
                        <label className="btn btn-sm">Load .txt file<input type="file" accept=".txt,text/plain" className="sr-only" onChange={loadTxt(di, vi)} /></label>
                        {v.loaded}
                      </span>
                    </Field>
                  </div>
                )
              })}
              <div><button type="button" className="btn btn-sm" onClick={() => update((f) => { const last = f.documents[di].versions.at(-1); f.documents[di].versions.push({ ...blankVersion(), author_role: last.author_role, text: last.text }) })}><Icon name="plus" size={14} />Add a later version</button></div>
            </div>
          ))}
          <div><button type="button" className="btn" onClick={() => update((f) => { f.documents.push(blankDoc()) })}><Icon name="plus" size={16} />Add document</button></div>
        </section>

        <section className="form-section" aria-labelledby="nc-rec">
          <h2 id="nc-rec">Research record</h2>
          {form.record_versions.map((v, i) => {
            const key = (name) => `record.${i}.${name}`
            return (
              <div key={i} className={i ? 'version-block' : undefined} style={{ display: 'grid', gap: 12 }}>
                <div className="doc-block-head">
                  <h3>Record version {i + 1}</h3>
                  {i > 0 && i === form.record_versions.length - 1 && <button type="button" className="btn btn-quiet btn-sm" onClick={() => update((f) => { f.record_versions.pop() })}>Remove version</button>}
                </div>
                <div className="grid-4">
                  <Field k={key('recorded_at')} label="Recorded at" problem={p(key('recorded_at'))} round={round}>
                    <input className="input" type="datetime-local" step="60" value={v.recorded_at} onChange={(e) => update((f) => { f.record_versions[i].recorded_at = e.target.value })} />
                  </Field>
                  <Field k={key('icans_reported')} label="ICANS reported" problem={p(key('icans_reported'))} round={round}>
                    <label className="check" style={{ minHeight: 38 }}><input type="checkbox" checked={v.icans_reported} onChange={(e) => update((f) => { f.record_versions[i].icans_reported = e.target.checked })} /> yes</label>
                  </Field>
                  <Field k={key('onset_date')} label="Onset date" hint={v.icans_reported ? 'Leave empty if the record has none' : 'Must be empty when no ICANS is reported'} problem={p(key('onset_date'))} round={round}>
                    <input className="input" type="date" value={v.onset_date} onChange={(e) => update((f) => { f.record_versions[i].onset_date = e.target.value })} />
                  </Field>
                  <Field k={key('max_grade')} label="Maximum grade" problem={p(key('max_grade'))} round={round}>
                    <select className="select" value={v.max_grade} onChange={(e) => update((f) => { f.record_versions[i].max_grade = e.target.value })}>
                      <option value="">empty</option>{[1, 2, 3, 4, 5].map((g) => <option key={g} value={g}>Grade {g}</option>)}
                    </select>
                  </Field>
                </div>
                {i > 0 && (
                  <Field k={key('change_reason')} label="Change reason" problem={p(key('change_reason'))} round={round}>
                    <input className="input" value={v.change_reason} onChange={(e) => update((f) => { f.record_versions[i].change_reason = e.target.value })} />
                  </Field>
                )}
              </div>
            )
          })}
          <div><button type="button" className="btn btn-sm" onClick={() => update((f) => { f.record_versions.push({ ...f.record_versions.at(-1), recorded_at: '', change_reason: '' }) })}><Icon name="plus" size={14} />Add a later record version</button></div>
        </section>

        <div className="form-foot">
          <button type="submit" className="btn btn-primary" disabled={saving}>{saving ? 'Saving…' : 'Save case'}</button>
          {summary && (
            <div key={round} className="form-problems problem-in" role="alert">
              {summary.text}
              {summary.general.map((g, i) => <div key={i}>{g}</div>)}
            </div>
          )}
        </div>
      </form>

      <dialog className="modal" ref={dialog} aria-labelledby="confirm-h">
        <h2 id="confirm-h">Synthetic data only</h2>
        <p>Do not load real patient records. Confirm that this case is fictional and contains no real names, dates of birth, record numbers or other identifiers.</p>
        <div className="row">
          <button type="button" className="btn" onClick={() => dialog.current?.close()}>Go back</button>
          <button type="button" className="btn btn-primary" onClick={save}>It is fictional: save</button>
        </div>
      </dialog>
    </div>
  )
}

function Field({ k, label, hint, problem, round, children }) {
  const id = `f-${k.replace(/\./g, '-')}`
  const kids = Array.isArray(children) ? children : [children]
  const [control, ...rest] = kids
  const enhanced = control && control.type !== 'label'
    ? cloneElement(control, { id, 'aria-invalid': problem ? true : undefined, 'aria-describedby': problem ? `${id}-p` : undefined })
    : control
  return (
    <div className="field" data-key={k} data-problem={problem ? '' : undefined}>
      <label htmlFor={control?.type !== 'label' ? id : undefined}>{label}</label>
      {enhanced}
      {rest}
      {hint && <span className="hint">{hint}</span>}
      {problem && <span key={round} id={`${id}-p`} className="problem-text problem-in"><Icon name="error" size={14} />{problem}</span>}
    </div>
  )
}
