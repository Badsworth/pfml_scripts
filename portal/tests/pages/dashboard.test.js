import Dashboard from "../../src/pages/dashboard";
import { mockRouter } from "next/router";
import { renderWithAppLogic } from "../test-utils";
import routes from "../../src/routes";

describe("Dashboard", () => {
  it("renders dashboard content", () => {
    mockRouter.pathname = routes.applications.dashboard;

    const { wrapper } = renderWithAppLogic(Dashboard, {
      diveLevels: 1,
    });
    expect(wrapper).toMatchSnapshot();
  });
});
