import routeWithParams, {
  createRouteWithQuery,
} from "../../src/utils/routeWithParams";

import routes from "../../src/routes";

describe("createRouteWithQuery", () => {
  let params, route, url;
  const hash = "test";

  beforeEach(() => {
    route = "/test/route";
  });
  it("adds a query string to a URL", () => {
    params = {
      a: "foo",
      b: "",
      c: true,
      d: false,
      e: 1,
      f: 0,
      g: "1",
      h: "0",
      i: "true",
      j: "false",
    };
    url = createRouteWithQuery(route, params);
    expect(url).toEqual(
      `${route}?a=foo&b=&c=true&d=false&e=1&f=0&g=1&h=0&i=true&j=false`
    );
  });
  it("omits query string if params are empty", () => {
    params = {};
    url = createRouteWithQuery(route, params);
    expect(url).toEqual(route);
  });
  it("ignores null or undefined params", () => {
    params = {
      a: "foo",
      b: null,
      c: "bar",
      d: undefined,
      e: "cat",
    };
    url = createRouteWithQuery(route, params);
    expect(url).toEqual(`${route}?a=foo&c=bar&e=cat`);

    params = {
      a: null,
      b: undefined,
    };
    url = createRouteWithQuery(route, params);
    expect(url).toEqual(route);
  });

  it("hash link is appended to URL as expected", () => {
    params = {
      param1: "value1",
      param2: "value2",
    };

    expect(createRouteWithQuery(route, params, hash)).toEqual(
      route + "?param1=value1&param2=value2#test"
    );

    expect(createRouteWithQuery(route, undefined, hash)).toEqual(
      route + "#test"
    );
  });
});

describe("routeWithParams", () => {
  it("creates a URL string of route and query parameters", () => {
    const routeName = "applications.name";
    const params = {
      param1: "value1",
      param2: "value2",
    };

    expect(routeWithParams(routeName, params)).toEqual(
      routes.applications.name + "?param1=value1&param2=value2"
    );
  });

  it("throws error if route does not exist", () => {
    console.error = jest.fn();

    const routeName = "applications.nomnom";

    const makeRoute = () => routeWithParams(routeName, { test: "value1" });
    expect(makeRoute).toThrowError();
  });
});
