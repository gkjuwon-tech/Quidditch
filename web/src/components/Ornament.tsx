/** A small golden snitch-glyph divider. */
export default function Ornament({ className = "" }: { className?: string }) {
  return (
    <div className={`hr-ornament ${className}`}>
      <svg width="34" height="18" viewBox="0 0 34 18" fill="none" aria-hidden>
        <path
          d="M1 9c5-6 9-6 12 0M33 9c-5-6-9-6-12 0"
          stroke="currentColor"
          strokeWidth="1.1"
          strokeLinecap="round"
        />
        <circle cx="17" cy="9" r="3.2" fill="currentColor" />
      </svg>
    </div>
  );
}
