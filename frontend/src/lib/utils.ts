/** 去掉小数末尾多余的 0，如 5.0000→5, 3.5000→3.5；0 值显示为空 */
export function fmtQty(n: any): string {
  const v = Number(n)
  if (isNaN(v) || v === 0) return ""
  return parseFloat(v.toFixed(2)).toString()
}

/** 金额格式化，保留 2 位小数并去掉末尾 0；0 值显示为空 */
export function fmtMoney(n: any): string {
  const v = Number(n)
  if (isNaN(v) || v === 0) return ""
  return parseFloat(v.toFixed(2)).toString()
}
