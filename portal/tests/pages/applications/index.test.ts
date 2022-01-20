import { MockBenefitsApplicationBuilder, renderPage } from "../../test-utils";
import { screen, within } from "@testing-library/react";
import { AppLogic } from "../../../src/hooks/useAppLogic";
import BenefitsApplicationCollection from "../../../src/models/BenefitsApplicationCollection";
import Index from "../../../src/pages/applications/index";
import routes from "../../../src/routes";
import userEvent from "@testing-library/user-event";

const inProgressClaim = new MockBenefitsApplicationBuilder()
  .id("mock_application_id_one")
  .create();

const submittedClaim = new MockBenefitsApplicationBuilder()
  .submitted()
  .create();
submittedClaim.fineos_absence_id = "NTN-111-ABS-03";

const completedClaim = new MockBenefitsApplicationBuilder()
  .completed()
  .create();

const setUpHelper = (appLogicHook: AppLogic) => {
  appLogicHook.benefitsApplications.benefitsApplications =
    new BenefitsApplicationCollection([]);
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

  it("displays Find Application action when feature flag is enabled", () => {
    const linkName = "Find my application";
    process.env.featureFlags = JSON.stringify({ channelSwitching: false });

    renderPage(Index, {
      pathname: routes.applications.index,
      addCustomSetup: (appLogicHook) => {
        setUpHelper(appLogicHook);
      },
    });

    expect(
      screen.queryByRole("link", { name: linkName })
    ).not.toBeInTheDocument();

    process.env.featureFlags = JSON.stringify({ channelSwitching: true });

    renderPage(Index, {
      pathname: routes.applications.index,
      addCustomSetup: (appLogicHook) => {
        setUpHelper(appLogicHook);
      },
    });

    expect(screen.queryByRole("link", { name: linkName })).toBeInTheDocument();
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

  it("user can view their in-progress + submitted applications", () => {
    renderPage(
      Index,
      {
        pathname: routes.applications.index,
        addCustomSetup: (appLogicHook) => {
          setUpHelper(appLogicHook);
          appLogicHook.documents.loadAll = jest.fn();
          appLogicHook.benefitsApplications.benefitsApplications =
            new BenefitsApplicationCollection([
              inProgressClaim,
              submittedClaim,
            ]);
        },
      },
      { query: {} }
    );

    expect(screen.getByText(/In-progress applications/)).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Application 1" })
    ).toBeInTheDocument();
  });

  it("displays completed applications", () => {
    renderPage(Index, {
      pathname: routes.applications.index,
      addCustomSetup: (appLogicHook) => {
        setUpHelper(appLogicHook);
        appLogicHook.documents.loadAll = jest.fn();
        appLogicHook.benefitsApplications.benefitsApplications =
          new BenefitsApplicationCollection([completedClaim]);
      },
    });

    expect(screen.getByText(/Submitted applications/)).toBeInTheDocument();
    expect(screen.getByText(/View your notices/)).toBeInTheDocument();
  });

  describe("When multiple claims of different statuses exist", () => {
    beforeEach(() => {
      renderPage(
        Index,
        {
          pathname: routes.applications.index,
          addCustomSetup: (appLogicHook) => {
            setUpHelper(appLogicHook);
            appLogicHook.documents.loadAll = jest.fn();
            appLogicHook.benefitsApplications.benefitsApplications =
              new BenefitsApplicationCollection([
                inProgressClaim,
                submittedClaim,
                completedClaim,
              ]);
          },
        },
        { query: {} }
      );
    });

    it("Displays Application Card for each claim", () => {
      const applicationCards = screen.getAllByRole("article");
      expect(applicationCards).toHaveLength(3);
      expect(screen.getByText(/Application 1/)).toBeInTheDocument();
      expect(
        screen.getAllByRole("link", { name: "Continue application" })
      ).toHaveLength(2);
      expect(screen.getByText(/NTN-111-ABS-01/)).toBeInTheDocument();
    });

    it("Displays headers for each section", () => {
      expect(screen.getByText(/In-progress applications/)).toBeInTheDocument();
      expect(screen.getByText(/Submitted applications/)).toBeInTheDocument();
    });

    it("Displays claims in expected order", () => {
      const [inProgClaim, subClaim, compClaim] = screen.getAllByRole("article");
      expect(
        within(inProgClaim).getByText(/Application 1/)
      ).toBeInTheDocument();
      expect(within(subClaim).getByText(/Application 2/)).toBeInTheDocument();
      expect(within(compClaim).getByText(/NTN-111-ABS-01/)).toBeInTheDocument();
    });
  });

  it("only loads documents for each claim once", () => {
    const inProgressClaim2 = new MockBenefitsApplicationBuilder().create();
    inProgressClaim2.application_id = "mock_application_id_two";

    const spy = jest.fn();

    renderPage(
      Index,
      {
        pathname: routes.applications.index,
        addCustomSetup: (appLogicHook) => {
          setUpHelper(appLogicHook);
          appLogicHook.documents.loadAll = spy;
          appLogicHook.benefitsApplications.benefitsApplications =
            new BenefitsApplicationCollection([
              inProgressClaim,
              inProgressClaim2,
            ]);
        },
      },
      { query: {} }
    );
    expect(spy).toHaveBeenCalledTimes(2);
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
            new BenefitsApplicationCollection([inProgressClaim]);
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
        addCustomSetup: setUpHelper,
      },
      { query: { applicationAssociated: "mock_id" } }
    );
    expect(
      screen.getByText(
        /Your application has been successfully linked to your account./
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
            new BenefitsApplicationCollection([inProgressClaim]);
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
            new BenefitsApplicationCollection([inProgressClaim]);
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
            new BenefitsApplicationCollection([inProgressClaim]);
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
            new BenefitsApplicationCollection([inProgressClaim]);
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
