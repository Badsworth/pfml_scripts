export const mockRouterEvents = [];

export const mockRouter = {
  pathname: "",
  query: {},
  asPath: "",
  push: jest.fn(),
  events: {
    on: (name, callback) => {
      mockRouterEvents.push({ name, callback });
    },
    off: jest.fn(),
  },
};

export function useRouter() {
  return mockRouter;
}

afterEach(() => {
  // Clear mock router events
  mockRouterEvents.length = 0;
});
