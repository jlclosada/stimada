/**
 * Format raw numeric IDs with their entity prefix for display.
 */
export function formatProjectId(id: string | null | undefined): string {
  if (!id) return "—";
  return id.startsWith("STM-") ? id : `STM-${id}`;
}

export function formatClientId(id: string | null | undefined): string {
  if (!id) return "—";
  return id.startsWith("CL-") ? id : `CL-${id}`;
}

export function formatContentMakerId(id: string | null | undefined): string {
  if (!id) return "—";
  return id.startsWith("CM-") ? id : `CM-${id}`;
}
