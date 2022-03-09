import Page from "../../../src/pages/employers/index";
import { renderPage } from "../../test-utils";

describe("/employers", () => {
  it("redirects to landing page", () => {
    let spy;

    renderPage(Page, {
      addCustomSetup: (appLogic) => {
        spy = jest.spyOn(appLogic.portalFlow, "goTo");
      },
    });

    expect(spy).toHaveBeenCalledWith("/", {}, { redirect: true });
  });
});
