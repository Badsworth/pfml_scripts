import NewApplication from "../../../../src/pages/employers/applications/new-application";
import { renderPage } from "../../../test-utils";
import routes from "../../../../src/routes";

describe("NewApplication", () => {
  it("redirects to status page when absence_id param is present", () => {
    let goToPageForSpy!: jest.SpyInstance;

    renderPage(NewApplication, {
      addCustomSetup: (appLogic) => {
        goToPageForSpy = jest.spyOn(appLogic.portalFlow, "goToPageFor");
      },
      pathname: routes.employers.newApplication,
    });

    expect(goToPageForSpy).not.toHaveBeenCalled();

    renderPage(
      NewApplication,
      {
        addCustomSetup: (appLogic) => {
          goToPageForSpy = jest.spyOn(appLogic.portalFlow, "goToPageFor");
        },
        pathname: routes.employers.newApplication,
      },
      {
        query: {
          absence_id: "mock-absence-id",
        },
      }
    );

    expect(goToPageForSpy).toHaveBeenCalledWith(
      "REDIRECT",
      {},
      { absence_id: "mock-absence-id" },
      { redirect: true }
    );
  });
});
