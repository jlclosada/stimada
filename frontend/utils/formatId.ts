/**
 * Format raw numeric IDs with their entity prefix for display.
 */
export function formatProjectId(id: string | null | undefined): string {
  if (!id) return "—";
  if (id.startsWith("DRAFT-")) return id;
  return id.startsWith("[PR]") ? id : `[PR] - ${id}`;
}

export function formatClientId(id: string | null | undefined): string {
  if (!id) return "—";
  return id.startsWith("[CL]") ? id : `[CL] - ${id}`;
}

export function formatContentMakerId(id: string | null | undefined): string {
  if (!id) return "—";
  return id.startsWith("[CM]") ? id : `[CM] - ${id}`;
}

export function formatBrandId(id: string | null | undefined): string {
  if (!id) return "—";
  return id.startsWith("[MR]") ? id : `[MR] - ${id}`;
}
