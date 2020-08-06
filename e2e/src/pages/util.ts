export function lookup<M extends { [k: string]: unknown }, K extends keyof M>(
  key: K,
  map: M
): M[K] {
  if (key in map) {
    return map[key];
  }
  throw new Error(`Unable to find ${key} in lookup map`);
}
