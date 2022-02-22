import { MockBenefitsApplicationBuilder, renderPage } from "../../test-utils";
import ApiResourceCollection from "src/models/ApiResourceCollection";
import { AppLogic } from "../../../src/hooks/useAppLogic";
import BenefitsApplication from "src/models/BenefitsApplication";
import Index from "../../../src/pages/applications/index";
import routes from "../../../src/routes";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

const inProgressClaim = new MockBenefitsApplicationBuilder()
  .id("mock_application_id_one")
  .create();

const submittedClaim = new MockBenefitsApplicationBuilder()
  .id("mock_application_id_two")
  .submitted()
  .create();
submittedClaim.fineos_absence_id = "NTN-111-ABS-03";

const completedClaim = new MockBenefitsApplicationBuilder()
  .id("mock_application_id_three")
  .completed()
  .create();

const setUpHelper = (appLogicHook: AppLogic) => {
  appLogicHook.benefitsApplications.benefitsApplications =
    new ApiResourceCollection<BenefitsApplication>("application_id", []);
  appLogicHook.benefitsApplications.loadPage = jest.fn();
};

describe("Applications", () => {
  it("redirects to getReady when no claims exist", () => {
    let goToSpy;

    renderPage(Index, {
      pathname: routes.applications.index,
      addCustomSetup: (appLogicHook) => {
        setUpHelper(appLogicHook);
        appLogicHook.benefitsApplications.isLoadingClaims = false;
        goToSpy = jest.spyOn(appLogicHook.portalFlow, "goTo");
      },
    });
    expect(goToSpy).toHaveBeenCalledWith("/applications/get-ready", {});
  });

  it("displays prompt for channel switching when feature flag is enabled", () => {
    const detailsLabel = "Did you start an application by phone?";
    process.env.featureFlags = JSON.stringify({ channelSwitching: false });

    renderPage(Index, {
      pathname: routes.applications.index,
      addCustomSetup: (appLogicHook) => {
        setUpHelper(appLogicHook);
      },
    });

    const detailsText = screen.queryByText(detailsLabel);
    expect(detailsText).not.toBeInTheDocument();

    process.env.featureFlags = JSON.stringify({ channelSwitching: true });

    renderPage(Index, {
      pathname: routes.applications.index,
      addCustomSetup: (appLogicHook) => {
        setUpHelper(appLogicHook);
      },
    });

    expect(screen.getByText(detailsLabel)).toBeInTheDocument();
  });

  it("passes mfaSetupSuccess value when it redirects to getReady", () => {
    let goToSpy;

    renderPage(
      Index,
      {
        pathname: routes.applications.index,
        addCustomSetup: (appLogicHook) => {
          setUpHelper(appLogicHook);
          appLogicHook.benefitsApplications.isLoadingClaims = false;
          goToSpy = jest.spyOn(appLogicHook.portalFlow, "goTo");
        },
      },
      { query: { smsMfaConfirmed: "true" } }
    );
    expect(goToSpy).toHaveBeenCalledWith("/applications/get-ready", {
      smsMfaConfirmed: "true",
    });
  });

  it("displays Application Card for each claim", () => {
    renderPage(
      Index,
      {
        pathname: routes.applications.index,
        addCustomSetup: (appLogicHook) => {
          setUpHelper(appLogicHook);
          appLogicHook.documents.loadAll = jest.fn();
          appLogicHook.benefitsApplications.benefitsApplications =
            new ApiResourceCollection<BenefitsApplication>("application_id", [
              inProgressClaim,
              submittedClaim,
              completedClaim,
            ]);
        },
      },
      { query: {} }
    );

    const applicationCards = screen.getAllByRole("article");
    expect(applicationCards).toHaveLength(3);
  });

  it("only loads documents for each submitted claim once", () => {
    const spy = jest.fn();

    renderPage(
      Index,
      {
        pathname: routes.applications.index,
        addCustomSetup: (appLogicHook) => {
          setUpHelper(appLogicHook);
          appLogicHook.documents.loadAll = spy;
          appLogicHook.benefitsApplications.benefitsApplications =
            new ApiResourceCollection<BenefitsApplication>("application_id", [
              submittedClaim,
            ]);
        },
      },
      { query: {} }
    );
    expect(spy).toHaveBeenCalledTimes(1);
  });

  it("displays success alert when uploaded absence id is present", () => {
    renderPage(
      Index,
      {
        pathname: routes.applications.index,
        addCustomSetup: (appLogicHook) => {
          setUpHelper(appLogicHook);
          appLogicHook.documents.loadAll = jest.fn();
          appLogicHook.benefitsApplications.benefitsApplications =
            new ApiResourceCollection<BenefitsApplication>("application_id", [
              inProgressClaim,
            ]);
        },
      },
      { query: { uploadedAbsenceId: "mock_id" } }
    );
    expect(
      screen.getByText(
        /Our Contact Center staff will review your documents for mock_id./
      )
    ).toBeInTheDocument();
  });

  it("displays success alert when claim was associated", () => {
    renderPage(
      Index,
      {
        pathname: routes.applications.index,
        addCustomSetup: (appLogicHook) => {
          setUpHelper(appLogicHook);
          appLogicHook.documents.loadAll = jest.fn();
          appLogicHook.benefitsApplications.benefitsApplications =
            new ApiResourceCollection<BenefitsApplication>("application_id", [
              submittedClaim,
            ]);
        },
      },
      { query: { applicationAssociated: submittedClaim.fineos_absence_id } }
    );
    expect(
      screen.getByText(
        /Application NTN-111-ABS-03 has been added to your account./
      )
    ).toBeInTheDocument();
  });

  it("displays success alert when user sets up SMS MFA", () => {
    renderPage(
      Index,
      {
        pathname: routes.applications.index,
        addCustomSetup: (appLogicHook) => {
          setUpHelper(appLogicHook);
          appLogicHook.documents.loadAll = jest.fn();
          appLogicHook.benefitsApplications.benefitsApplications =
            new ApiResourceCollection<BenefitsApplication>("application_id", [
              inProgressClaim,
            ]);
        },
      },
      { query: { smsMfaConfirmed: "true" } }
    );
    expect(screen.getByRole("region")).toMatchSnapshot();
  });

  describe("Pagination Navigation", () => {
    it("does not display when there is only 1 page of applications", () => {
      renderPage(Index, {
        pathname: routes.applications.index,
        addCustomSetup: (appLogicHook) => {
          setUpHelper(appLogicHook);
          appLogicHook.documents.loadAll = jest.fn();
          appLogicHook.benefitsApplications.benefitsApplications =
            new ApiResourceCollection<BenefitsApplication>("application_id", [
              inProgressClaim,
            ]);
        },
      });

      expect(
        screen.queryByRole("button", { name: /next/i })
      ).not.toBeInTheDocument();
    });

    it("does display when there is more than 1 page of applications", () => {
      renderPage(Index, {
        pathname: routes.applications.index,
        addCustomSetup: (appLogicHook) => {
          setUpHelper(appLogicHook);
          appLogicHook.documents.loadAll = jest.fn();
          appLogicHook.benefitsApplications.benefitsApplications =
            new ApiResourceCollection<BenefitsApplication>("application_id", [
              inProgressClaim,
            ]);
          appLogicHook.benefitsApplications.paginationMeta = {
            total_records: 50,
            total_pages: 2,
            page_offset: 1,
            page_size: 1,
            order_by: "created_at",
            order_direction: "ascending",
          };
        },
      });

      expect(
        screen.queryByRole("button", { name: /next/i })
      ).toBeInTheDocument();
    });

    it("changes page_offset when clicked", () => {
      let updateQuerySpy;

      renderPage(Index, {
        pathname: routes.applications.index,
        addCustomSetup: (appLogicHook) => {
          setUpHelper(appLogicHook);
          appLogicHook.documents.loadAll = jest.fn();
          appLogicHook.benefitsApplications.benefitsApplications =
            new ApiResourceCollection<BenefitsApplication>("application_id", [
              inProgressClaim,
            ]);
          appLogicHook.benefitsApplications.paginationMeta = {
            total_records: 50,
            total_pages: 2,
            page_offset: 1,
            page_size: 1,
            order_by: "created_at",
            order_direction: "ascending",
          };
          updateQuerySpy = jest.spyOn(appLogicHook.portalFlow, "updateQuery");
        },
      });

      userEvent.click(screen.getByRole("button", { name: /next/i }));

      expect(updateQuerySpy).toHaveBeenCalledWith({
        page_offset: "2",
      });
    });
  });
});
