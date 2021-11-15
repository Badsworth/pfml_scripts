/**
 * Create a mock function. Uses jest.fn() if called in the Jest environment.
 */
function createMockFn(implementation?: (...args: unknown[]) => unknown) {
  if (typeof jest !== "undefined") {
    return jest.fn().mockImplementation(implementation);
  }

  return () => (implementation ? implementation() : undefined);
}

export default createMockFn;
