/**
 * Format timestamp to DD/MM/YYYY HH:MM:SS format
 * @param {string | Date} timestamp - ISO format timestamp or Date object
 * @returns {string} Formatted timestamp or original value if parsing fails
 */
export function formatTimestamp(timestamp) {
  if (!timestamp) return '—'

  try {
    // Parse the timestamp - handle both ISO strings and Date objects
    const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp

    // Check if date is valid
    if (!(date instanceof Date) || isNaN(date)) {
      return String(timestamp)
    }

    // Format as DD/MM/YYYY HH:MM:SS
    const day = String(date.getDate()).padStart(2, '0')
    const month = String(date.getMonth() + 1).padStart(2, '0')
    const year = date.getFullYear()
    const hours = String(date.getHours()).padStart(2, '0')
    const minutes = String(date.getMinutes()).padStart(2, '0')
    const seconds = String(date.getSeconds()).padStart(2, '0')

    return `${day}/${month}/${year} ${hours}:${minutes}:${seconds}`
  } catch (e) {
    // If parsing fails, return the original value
    return String(timestamp)
  }
}
