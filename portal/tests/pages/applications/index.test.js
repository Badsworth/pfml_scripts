import { MockBenefitsApplicationBuilder, renderPage } from "../../test-utils";
import BenefitsApplicationCollection from "../../../src/models/BenefitsApplicationCollection";
import Index from "../../../src/pages/applications/index";
import { mockRouter } from "next/router";
import routes from "../../../src/routes";
import { screen } from "@testing-library/react";

describe("Applications", () => {
  let appLogic;

  beforeEach(() => {
    mockRouter.pathname = routes.applications.index;
  });

  it("redirects to getReady when no claims exist", () => {
    let appLogic, goToSpy;

    renderPage(Index, {
      addCustomSetup: (appLogicHook) => {
        appLogic = appLogicHook;
        appLogic.benefitsApplications.loadAll = jest.fn(() => {
          return Promise.resolve();
        });
        appLogic.benefitsApplications.hasLoadedAll = true;
        appLogic.benefitsApplications.benefitsApplications =
          new BenefitsApplicationCollection([]);
        goToSpy = jest.spyOn(appLogic.portalFlow, "goTo");
      },
    });
    expect(goToSpy).toHaveBeenCalledWith("/applications/get-ready");
  });

  it("user can view their in-progress + submitted applications", () => {
    const exampleInProgressApplication =
      new MockBenefitsApplicationBuilder().create();
    exampleInProgressApplication.application_id = "mock_application_id_one";
    exampleInProgressApplication.fineos_absence_id = "NTN-111-ABS-02";
    const exampleSubmittedApplication = new MockBenefitsApplicationBuilder()
      .submitted()
      .create();

    renderPage(Index, {
      addCustomSetup: (appLogicHook) => {
        appLogic = appLogicHook;
        appLogic.documents.loadAll = jest.fn();
        appLogic.benefitsApplications.loadAll = jest.fn(() => {
          return Promise.resolve();
        });
        appLogic.benefitsApplications.hasLoadedAll = true;
        appLogic.benefitsApplications.benefitsApplications =
          new BenefitsApplicationCollection([
            exampleInProgressApplication,
            exampleSubmittedApplication,
          ]);
      },
    });

    expect(screen.getByText(/In-progress applications/)).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "NTN-111-ABS-02" })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "NTN-111-ABS-01" })
    ).toBeInTheDocument();
  });

  it("displays completed applications", () => {
    renderPage(Index, {
      addCustomSetup: (appLogicHook) => {
        appLogic = appLogicHook;
        appLogic.documents.loadAll = jest.fn();
        appLogic.benefitsApplications.loadAll = jest.fn(() => {
          return Promise.resolve();
        });
        appLogic.benefitsApplications.hasLoadedAll = true;
        appLogic.benefitsApplications.benefitsApplications =
          new BenefitsApplicationCollection([
            new MockBenefitsApplicationBuilder().completed().create(),
          ]);
      },
    });

    expect(screen.getByText(/Submitted applications/)).toBeInTheDocument();
    expect(screen.getByText(/Download your notices/)).toBeInTheDocument();
  });
});
