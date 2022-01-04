export function parseEcrAccountId(registry: string): string {
  return registry.split('.')[0];
}

export function parseEcrRegion(registry: string): string {
  return registry.split('.')[3];
}
