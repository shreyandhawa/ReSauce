// A small authored icon set: 20×20 grid, 1.75 stroke, round joins. Decorative unless labelled.
// Outcome shapes match the marks on the pipeline stage: ◆ discrepancy, ▲ needs review,
// ● no discrepancy detected, ○ not verified, ✕ could not run.
const PATHS = {
  diamond: <path d="M10 2.6 17.4 10 10 17.4 2.6 10Z" fill="currentColor" stroke="none" />,
  triangle: <path d="M10 3.2 17.6 16.4H2.4Z" fill="currentColor" stroke="none" />,
  dot: <circle cx="10" cy="10" r="6.4" fill="currentColor" stroke="none" />,
  ring: <circle cx="10" cy="10" r="6" />,
  cross: <path d="m5 5 10 10M15 5 5 15" strokeWidth="2.4" />,
  flag: <><path d="M5 17.5V3" /><path d="M5 3.5h9.5l-2 3.5 2 3.5H5" /></>,
  reviewed: <><circle cx="10" cy="10" r="7.2" /><path d="m6.8 10.2 2.3 2.3 4.3-4.6" /></>,
  error: <><circle cx="10" cy="10" r="7.2" /><path d="m7.2 7.2 5.6 5.6M12.8 7.2l-5.6 5.6" /></>,
  queue: <><path d="M3 11.5h3.5l1.2 2h4.6l1.2-2H17" /><path d="M4.5 4h11L17 11.5V16H3v-4.5Z" /></>,
  export: <><path d="M10 3v9.5" /><path d="m6.5 9 3.5 3.5L13.5 9" /><path d="M4 14.5V17h12v-2.5" /></>,
  plus: <path d="M10 4.5v11M4.5 10h11" />,
  play: <path d="M6.5 4.2v11.6l9.2-5.8Z" fill="currentColor" />,
  pause: <path d="M7 4.5v11M13 4.5v11" strokeWidth="2.6" />,
  skip: <><path d="M4.5 4.5v11l7.5-5.5Z" fill="currentColor" /><path d="M15.5 4.5v11" strokeWidth="2.2" /></>,
  folder: <path d="M2.8 5.5c0-.6.4-1 1-1h4l1.6 1.8h6.8c.6 0 1 .4 1 1V15c0 .6-.4 1-1 1H3.8c-.6 0-1-.4-1-1Z" />,
  search: <><circle cx="8.8" cy="8.8" r="5" /><path d="m12.6 12.6 4 4" /></>,
  chevron: <path d="m8 5 5 5-5 5" />,
  back: <path d="m12 5-5 5 5 5" />,
  print: <><path d="M6 7V3.5h8V7" /><rect x="3" y="7" width="14" height="6.5" rx="1" /><path d="M6 11.5h8V17H6Z" /></>,
  shield: <path d="M10 2.8 16 5v4.6c0 3.6-2.6 6.3-6 7.6-3.4-1.3-6-4-6-7.6V5Z" />,
  theme: <><circle cx="10" cy="10" r="7" /><path d="M10 3a7 7 0 0 0 0 14Z" fill="currentColor" /></>,
  zoomin: <><circle cx="9" cy="9" r="5.6" /><path d="m13.2 13.2 3.8 3.8M9 6.6v4.8M6.6 9h4.8" /></>,
  zoomout: <><circle cx="9" cy="9" r="5.6" /><path d="m13.2 13.2 3.8 3.8M6.6 9h4.8" /></>,
  fit: <path d="M3.5 7.5v-4h4M16.5 7.5v-4h-4M3.5 12.5v4h4M16.5 12.5v4h-4" />,
  numbers: <path d="M7.6 3.5 6.2 16.5M13.8 3.5l-1.4 13M3.5 7.5h13M3 12.5h13" />,
  network: <><circle cx="4.5" cy="5" r="1.8" /><circle cx="4.5" cy="15" r="1.8" /><circle cx="15.5" cy="10" r="2.2" /><path d="M6.2 5.6 13.4 9.2M6.2 14.4l7.2-3.6" /></>,
  list: <path d="M7 5h10M7 10h10M7 15h10M3.2 5h.6M3.2 10h.6M3.2 15h.6" strokeWidth="2" />,
  close: <path d="m5 5 10 10M15 5 5 15" />,
  menu: <path d="M3.5 6.5h13M3.5 13.5h13" strokeWidth="2" />,
  open: <><path d="M11.5 3.5h5v5" /><path d="M16.5 3.5 9 11" /><path d="M14.5 11.5v4c0 .6-.4 1-1 1h-9c-.6 0-1-.4-1-1v-9c0-.6.4-1 1-1h4" /></>,
  import: <><path d="M10 12.5V3" /><path d="m6.5 6.5 3.5-3.5 3.5 3.5" /><path d="M4 11v5.5h12V11" /></>,
}
// The finding and status names draw the outcome shapes, so a sign and a mark always match.
Object.assign(PATHS, { discrepancy: PATHS.diamond, review: PATHS.triangle, clear: PATHS.dot, notrun: PATHS.ring })

export default function Icon({ name, size = 18, label }) {
  return (
    <svg width={size} height={size} viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.75"
      strokeLinecap="round" strokeLinejoin="round" role={label ? 'img' : undefined} aria-label={label}
      aria-hidden={label ? undefined : true} focusable="false">
      {PATHS[name]}
    </svg>
  )
}

/**
 * The ReSauce mark: records entering on the left, converging through one node, and branching into
 * two outcomes: one grounded (a filled square), one flagged (a diamond). Original drawing.
 */
export function Logo({ size = 26 }) {
  return (
    <svg className="logo" width={size} height={size} viewBox="0 0 32 32" aria-hidden="true" focusable="false">
      <rect width="32" height="32" rx="9" fill="currentColor" />
      <g fill="none" stroke="var(--logo-ink)" strokeWidth="2.2" strokeLinecap="round">
        <path d="M6.5 9.5c4 0 5 6.5 9.5 6.5M6.5 22.5c4 0 5-6.5 9.5-6.5M16 16h3.5" />
        <path d="M19.5 16c2.6 0 2.8-6 5.2-6M19.5 16c2.6 0 2.8 6 5.2 6" />
      </g>
      <circle cx="16" cy="16" r="2.6" fill="var(--logo-ink)" />
      <path d="M25.6 6.6 28.4 9.4 25.6 12.2 22.8 9.4Z" fill="var(--logo-signal)" />
      <rect x="23" y="19.6" width="5" height="5" rx="1.2" fill="var(--logo-ink)" />
    </svg>
  )
}
