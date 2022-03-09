/**
 * @file Common next/router mocks for use in Storybook and Tests
 */
import Router from "next/router";
import createMockFn from "./createMockFn";

export interface MockRouterEvent {
  name: string;
  callback: RouterEventCallback;
}

export const mockRouterEvents: MockRouterEvent[] = [];

type RouterEventCallback = (...args: unknown[]) => unknown;

// @ts-expect-error Router mock is missing properties we don't currently reference
export const mockRouter = {
  locale: "en-US",
  route: "/",
  pathname: "",
  query: {},
  asPath: "",
  back: createMockFn(),
  beforePopState: createMockFn(),
  prefetch: createMockFn(() => Promise.resolve()),
  push: createMockFn(),
  replace: createMockFn(),
  reload: createMockFn(),
  events: {
    on: (name: string, callback: RouterEventCallback) => {
      mockRouterEvents.push({ name, callback });
    },
    off: createMockFn(),
  },
  isFallback: false,
} as typeof Router.router;

export function useRouter() {
  return mockRouter;
}
