import { useMemo, useState } from 'react'
import { api } from '../api.js'
import { CategoryTag, Loading, Problem, Segmented } from '../components/Bits.jsx'
import { FIELDS, FIELD_NAMES } from '../lib/format.js'
import { useLoad } from '../lib/hooks.js'

const DISAGREE_OPTIONS = [['all', 'All cases'], ['any', 'A method disagrees'], ['resauce', 'ReSauce disagrees'], ['baseline_a', 'Baseline A disagrees']]

export default function Cases() {
  const { data, error, loading } = useLoad(() => api.cases(), [])
  const [split, setSplit] = useState('all')
  const [disagree, setDisagree] = useState('all')

  const splitOptions = useMemo(() => {
    if (!data) return []
    const seen = new Map()
    for (const c of data.cases) seen.set(c.split, c.split_title)
    return [['all', 'All splits'], ...seen]
  }, [data])

  const rows = useMemo(() => {
    if (!data) return []
    return data.cases.filter((c) => {
      if (split !== 'all' && c.split !== split) return false
      if (disagree === 'all') return true
      const methods = disagree === 'any' ? ['resauce', 'baseline_a'] : [disagree]
      return methods.some((m) => c.agreement[m] === 'disagrees')
    })
  }, [data, split, disagree])

  if (error) return <Problem title="The case list could not be loaded" error={error} />
  if (loading) return <Loading label="Loading cases" />
  const title = data.methods

  return (
    <div className="page cases">
      <div className="page-head">
        <h1>Cases</h1>
        <p className="page-sub">
          Every case with its split and its category per field: the reference answer, ReSauce and Baseline A.
          A marked cell differs from the reference. Open a case to run the pipeline on it live.
        </p>
      </div>

      <div className="filters">
        <Segmented label="Split" options={splitOptions} value={split} onChange={setSplit} />
        <Segmented label="Agreement with the reference" options={DISAGREE_OPTIONS} value={disagree} onChange={setDisagree} />
        <p className="filter-count" role="status">{rows.length} of {data.cases.length} cases</p>
      </div>

      <div className="table-scroll">
        <table className="case-table">
          <thead>
            <tr>
              <th scope="col" rowSpan={2}>Case</th>
              <th scope="col" rowSpan={2}>Split</th>
              {FIELDS.map((f) => <th key={f} scope="colgroup" colSpan={3} className="field-head">{FIELD_NAMES[f]}</th>)}
              <th scope="col" rowSpan={2}>Agreement</th>
            </tr>
            <tr>
              {FIELDS.flatMap((f) => [
                <th key={f + 'r'} scope="col">Reference</th>,
                <th key={f + 'a'} scope="col">{title.resauce}</th>,
                <th key={f + 'b'} scope="col">{title.baseline_a}</th>,
              ])}
            </tr>
          </thead>
          <tbody>
            {rows.map((c) => (
              <tr key={c.case_id} onClick={(e) => { if (e.target.tagName !== 'A') window.location.hash = `#/case/${c.case_id}` }}>
                <th scope="row"><a href={`#/case/${c.case_id}`} className="mono">{c.case_id}</a></th>
                <td className="split-cell">{c.split_title}</td>
                {FIELDS.flatMap((f) => {
                  const ref = c.reference?.fields?.[f]
                  return [
                    <td key={f + 'r'}><CategoryTag category={ref} /></td>,
                    <td key={f + 'a'}><CategoryTag category={c.resauce.error ? 'error' : c.resauce[f]} against={ref} /></td>,
                    <td key={f + 'b'}><CategoryTag category={c.baseline_a.error ? 'error' : c.baseline_a[f]} against={c.reference?.out_of_scope ? undefined : ref} /></td>,
                  ]
                })}
                <td>
                  <div className="agree-cell">
                    <Agreement label={title.resauce} value={c.agreement.resauce} />
                    <Agreement label={title.baseline_a} value={c.agreement.baseline_a} />
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {rows.length === 0 && <p className="empty">No case matches these filters.</p>}
      <p className="section-note">
        Agreement uses the evaluation’s rules: in scope, every field’s category equals the reference category; out of scope,
        the case is flagged out of scope with the reference’s reason. Baseline A cannot flag a case out of scope, so it shows “n/a” there.
      </p>
    </div>
  )
}

const AGREEMENT_TEXT = { agrees: 'agrees', disagrees: 'disagrees', 'n/a': 'n/a', error: 'error' }

function Agreement({ label, value }) {
  if (!value) return null
  return <span className={`agree agree-${value.replace('/', '')}`}>{label}: {AGREEMENT_TEXT[value]}</span>
}
