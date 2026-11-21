import { RISK } from '../constants/riskLevels'
export const riskColor = (level) => RISK[level]?.color || '#64748b'
