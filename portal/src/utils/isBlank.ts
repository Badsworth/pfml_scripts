function isBlank(value?: unknown): value is undefined | null | "" {
  return value === undefined || value === null || value === "";
}

export default isBlank;
