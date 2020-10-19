import Index from "../../src/pages/index";
import { mockRouter } from "next/router";
import { renderWithAppLogic } from "../test-utils";
import routes from "../../src/routes";

describe("Index", () => {
  it("renders dashboard content", () => {
    mockRouter.pathname = routes.home;

    const { wrapper } = renderWithAppLogic(Index, {
      diveLevels: 1,
    });
    expect(wrapper).toMatchSnapshot();
  });
});
