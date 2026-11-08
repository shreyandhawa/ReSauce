// A small authored icon set: 20×20 grid, 1.75 stroke, round joins. Decorative unless labelled.
const PATHS = {
  discrepancy: <path d="M10 2.8 17.2 10 10 17.2 2.8 10Z" fill="currentColor" stroke="none" />,
  review: <><circle cx="10" cy="10" r="7.2" /><path d="M7.9 7.9a2.2 2.2 0 1 1 3 2.1c-.6.3-.9.8-.9 1.4v.3" /><circle cx="10" cy="14.2" r=".4" fill="currentColor" /></>,
  flag: <><path d="M5 17.5V3" /><path d="M5 3.5h9.5l-2 3.5 2 3.5H5" /></>,
  clear: <path d="m4.5 10.5 3.5 3.5 7.5-8" />,
  reviewed: <><circle cx="10" cy="10" r="7.2" /><path d="m6.8 10.2 2.3 2.3 4.3-4.6" /></>,
  notrun: <><circle cx="10" cy="10" r="7.2" strokeDasharray="2.4 2.2" /></>,
  error: <><path d="M10 3 17.5 16.5h-15Z" /><path d="M10 8.2v3.6" /><circle cx="10" cy="14" r=".4" fill="currentColor" /></>,
  cases: <><rect x="3" y="3.5" width="14" height="13" rx="1.5" /><path d="M3 8h14M7.5 8v8.5" /></>,
  queue: <><path d="M3 11.5h3.5l1.2 2h4.6l1.2-2H17" /><path d="M4.5 4h11L17 11.5V16H3v-4.5Z" /></>,
  audit: <><path d="M6 3.5h8.5V16.5H5.5V4Z" /><path d="M8 7.5h4.5M8 10.5h4.5M8 13.5h2.5" /></>,
  export: <><path d="M10 3v9.5" /><path d="m6.5 9 3.5 3.5L13.5 9" /><path d="M4 14.5V17h12v-2.5" /></>,
  validation: <><path d="M3.5 16.5h13" /><path d="M5.5 16.5V10M10 16.5V5.5M14.5 16.5V8.5" /></>,
  about: <><circle cx="10" cy="10" r="7.2" /><path d="M10 9v4.5" /><circle cx="10" cy="6.4" r=".4" fill="currentColor" /></>,
  plus: <path d="M10 4.5v11M4.5 10h11" />,
  play: <path d="M6.5 4.5v11l9-5.5Z" />,
  folder: <path d="M2.8 5.5c0-.6.4-1 1-1h4l1.6 1.8h6.8c.6 0 1 .4 1 1V15c0 .6-.4 1-1 1H3.8c-.6 0-1-.4-1-1Z" />,
  search: <><circle cx="8.8" cy="8.8" r="5" /><path d="m12.6 12.6 4 4" /></>,
  chevron: <path d="m8 5 5 5-5 5" />,
  back: <path d="m12 5-5 5 5 5" />,
  print: <><path d="M6 7V3.5h8V7" /><rect x="3" y="7" width="14" height="6.5" rx="1" /><path d="M6 11.5h8V17H6Z" /></>,
  shield: <path d="M10 2.8 16 5v4.6c0 3.6-2.6 6.3-6 7.6-3.4-1.3-6-4-6-7.6V5Z" />,
  theme: <><circle cx="10" cy="10" r="7" /><path d="M10 3a7 7 0 0 0 0 14Z" fill="currentColor" /></>,
}

export default function Icon({ name, size = 18, label }) {
  return (
    <svg width={size} height={size} viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.75"
      strokeLinecap="round" strokeLinejoin="round" role={label ? 'img' : undefined} aria-label={label}
      aria-hidden={label ? undefined : true} focusable="false">
      {PATHS[name]}
    </svg>
  )
}
