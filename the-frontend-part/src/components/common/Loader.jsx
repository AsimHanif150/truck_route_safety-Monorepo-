export default function Loader({ label = 'Planning your safest routes…' }) {
  return (
    <div className="loader">
      <span className="spinner" />
      {label}
    </div>
  )
}
