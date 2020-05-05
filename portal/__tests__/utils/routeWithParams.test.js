import routeWithParams from "../../src/utils/routeWithParams";
import routes from "../../src/routes";

describe("routeWithParams", () => {
  it("creates a URL string of route and query parameters", () => {
    const routeName = "claims.name";
    const params = {
      param1: "value1",
      param2: "value2",
    };

    expect(routeWithParams(routeName, params)).toEqual(
      routes.claims.name + "?param1=value1&param2=value2"
    );
  });

  it("throws error if route does not exist", () => {
    console.error = jest.fn();

    const routeName = "claims.nomnom";

    const makeRoute = () => routeWithParams(routeName, { test: "value1" });
    expect(makeRoute).toThrowError();
  });
});
