export const mockRouterEvents = [];

export const mockRouter = {
  pathname: "",
  query: {},
  asPath: "",
  push: jest.fn(),
  replace: jest.fn(),
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
  mockRouter.pathname = "";

  // Clear mock router events
  mockRouterEvents.length = 0;
});
