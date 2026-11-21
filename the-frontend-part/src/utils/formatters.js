export const formatDuration = (mins) => {
  if (!Number.isFinite(Number(mins))) return '—'
  const h = Math.floor(mins / 60),
    m = Math.round(mins % 60)
  return `${h}h ${m}m`
}
export const formatEta = (value) =>
  value
    ? new Date(value).toLocaleString([], {
        month: 'short',
        day: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
      })
    : '—'
export const formatNumber = (n) => Number(n || 0).toLocaleString()
