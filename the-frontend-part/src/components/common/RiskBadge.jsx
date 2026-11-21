import { RISK } from '../../constants/riskLevels'
export default function RiskBadge({ level = 'low' }) {
  const r = RISK[level] || RISK.low
  return <span className={`risk-badge risk-${level}`}>{r.label}</span>
}
