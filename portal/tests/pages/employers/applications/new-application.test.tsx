import NewApplication from "../../../../src/pages/employers/applications/new-application";
import { renderPage } from "../../../test-utils";
import routes from "../../../../src/routes";

describe("NewApplication", () => {
  it("redirects to status page", () => {
    let goToPageForSpy!: jest.SpyInstance;

    renderPage(NewApplication, {
      addCustomSetup: (appLogic) => {
        goToPageForSpy = jest.spyOn(appLogic.portalFlow, "goToPageFor");
      },
      pathname: routes.employers.newApplication,
    });

    expect(goToPageForSpy).toHaveBeenCalledWith(
      "REDIRECT",
      {},
      {},
      { redirect: true }
    );
  });
});
