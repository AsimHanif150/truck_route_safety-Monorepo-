export default function NotFound() {
  return (
    <main className="empty-state">
      <span className="eyebrow">404 · PAGE NOT FOUND</span>
      <h1>We couldn't find that page.</h1>
      <p>The address may be incorrect, or the page may have moved.</p>
      <a className="text-button" href="/">
        Return to trip planner →
      </a>
    </main>
  )
}
