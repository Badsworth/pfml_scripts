import { MockBenefitsApplicationBuilder, renderPage } from "../../test-utils";
import ApiResourceCollection from "src/models/ApiResourceCollection";
import { AppLogic } from "../../../src/hooks/useAppLogic";
import BenefitsApplication from "src/models/BenefitsApplication";
import Index from "../../../src/pages/applications/index";
import dayjs from "dayjs";
import formatDate from "src/utils/formatDate";
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

  it("displays benefit year notice when FF is enabled and current benefit year exists", () => {
    process.env.featureFlags = JSON.stringify({
      splitClaimsAcrossBY: true,
    });

    const startDate = new Date();
    const endDate = dayjs(startDate).add(1, "year");

    renderPage(Index, {
      pathname: routes.applications.index,
      addCustomSetup: (appLogicHook) => {
        setUpHelper(appLogicHook);
        appLogicHook.benefitYears.loadBenefitYears = jest.fn();
        appLogicHook.benefitYears.getCurrentBenefitYear = jest
          .fn()
          .mockReturnValue({
            benefit_year_start_date: startDate.toUTCString(),
            benefit_year_end_date: endDate.toDate().toUTCString(),
            employee_id: "2a340cf8-6d2a-4f82-a075-73588d003f8f",
            current_benefit_year: true,
          });
      },
    });

    const byText = new RegExp(
      `is ${formatDate(startDate.toISOString()).short()} to ${formatDate(
        endDate.toISOString()
      ).short()}. Most Massachusetts employees are eligible for up to 26 weeks of combined family and medical leave per benefit year.`
    );
    expect(screen.getByText(byText)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "benefit year" })).toHaveAttribute(
      "href",
      "https://www.mass.gov/info-details/types-of-paid-family-and-medical-leave#important-terms-to-know-"
    );

    expect(
      screen.getByRole("link", {
        name: "application review and approval process",
      })
    ).toBeInTheDocument();

    expect(
      screen.getByRole("link", {
        name: "application review and approval process",
      })
    ).toHaveAttribute("href", "https://mass.gov/pfml/application-timeline");
  });

  it("shows the split application alert when the query parameter is set and the first application is submitted", () => {
    const originalApplication = new MockBenefitsApplicationBuilder()
      .id("1")
      .splitIntoApplicationId("2")
      .continuous()
      .submitted()
      .create();
    const splitApplication = new MockBenefitsApplicationBuilder()
      .id("2")
      .splitFromApplicationId("1")
      .continuous({
        leave_period_id: "mock-leave-period-id-2",
        start_date: "2022-06-02",
        end_date: "2022-08-01",
      })
      .computedEarliestSubmissionDate("2022-06-02")
      .create();
    renderPage(
      Index,
      {
        pathname: routes.applications.index,
        addCustomSetup: (appLogicHook) => {
          setUpHelper(appLogicHook);
          appLogicHook.documents.loadAll = jest.fn();
          appLogicHook.benefitsApplications.isLoadingClaims = false;
          appLogicHook.benefitsApplications.benefitsApplications =
            new ApiResourceCollection<BenefitsApplication>("application_id", [
              originalApplication,
              splitApplication,
            ]);
        },
      },
      { query: { applicationWasSplitInto: "2" } }
    );

    const successPartOne = screen.queryByText(
      /You successfully submitted Part 1. Submit Parts 2 and 3 so that we can review your application./
    );
    const partOneLeaveDates = screen.queryByText(
      /leave dates from 1\/1\/2022 to 6\/1\/2022/
    );

    const submitPartTwo = screen.queryByText(
      /You will be able to submit Part 1 of your new benefit year application on/
    );
    const partTwoLeaveDates = screen.queryByText(
      /leave dates from 6\/2\/2022 to 8\/1\/2022/
    );

    const submitPartTwoDate = screen.queryAllByText("6/2/2022");

    expect(successPartOne).toBeInTheDocument();
    expect(partOneLeaveDates).toBeInTheDocument();
    expect(submitPartTwo).toBeInTheDocument();
    // Also displayed in the application card
    expect(submitPartTwoDate).toHaveLength(2);
    expect(partTwoLeaveDates).toBeInTheDocument();
  });

  it("shows the split application alert when the query parameter is set and both applications are submitted", () => {
    const originalApplication = new MockBenefitsApplicationBuilder()
      .id("1")
      .splitIntoApplicationId("2")
      .continuous()
      .submitted()
      .create();
    const splitApplication = new MockBenefitsApplicationBuilder()
      .id("2")
      .splitFromApplicationId("1")
      .continuous({
        leave_period_id: "mock-leave-period-id-2",
        start_date: "2022-06-02",
        end_date: "2022-08-01",
      })
      .submitted()
      .create();
    renderPage(
      Index,
      {
        pathname: routes.applications.index,
        addCustomSetup: (appLogicHook) => {
          setUpHelper(appLogicHook);
          appLogicHook.documents.loadAll = jest.fn();
          appLogicHook.benefitsApplications.isLoadingClaims = false;
          appLogicHook.benefitsApplications.benefitsApplications =
            new ApiResourceCollection<BenefitsApplication>("application_id", [
              originalApplication,
              splitApplication,
            ]);
        },
      },
      { query: { applicationWasSplitInto: "2" } }
    );

    const successPartOneAndTwo = screen.queryByText(
      "You successfully submitted Part 1. Your application was split into two, one for each benefit year. Submit Parts 2 and 3 so that we can review your applications."
    );

    expect(successPartOneAndTwo).toBeInTheDocument();
  });

  it("does not display the split application alert if the relevant applications are not found", () => {
    const originalApplication = new MockBenefitsApplicationBuilder()
      .id("1")
      .splitIntoApplicationId("2")
      .continuous()
      .submitted()
      .create();
    const splitApplication = new MockBenefitsApplicationBuilder()
      .id("2")
      .splitFromApplicationId("1")
      .continuous({
        leave_period_id: "mock-leave-period-id-2",
        start_date: "2022-06-02",
        end_date: "2022-08-01",
      })
      .submitted()
      .create();
    renderPage(
      Index,
      {
        pathname: routes.applications.index,
        addCustomSetup: (appLogicHook) => {
          setUpHelper(appLogicHook);
          appLogicHook.documents.loadAll = jest.fn();
          appLogicHook.benefitsApplications.isLoadingClaims = false;
          appLogicHook.benefitsApplications.benefitsApplications =
            new ApiResourceCollection<BenefitsApplication>("application_id", [
              originalApplication,
              splitApplication,
            ]);
        },
      },
      { query: { applicationWasSplitInto: "400" } }
    );

    const successPartOne = screen.queryByText(
      /You successfully submitted Part 1. Submit Parts 2 and 3 so that we can review your application./
    );
    const successPartOneAndTwo = screen.queryByText(
      "You successfully submitted Part 1. Your application was split into two, one for each benefit year. Submit Parts 2 and 3 so that we can review your applications."
    );

    expect(successPartOneAndTwo).not.toBeInTheDocument();
    expect(successPartOne).not.toBeInTheDocument();
  });

  it("does not display the split application alert if the applications are not loaded", () => {
    renderPage(
      Index,
      {
        pathname: routes.applications.index,
        addCustomSetup: (appLogicHook) => {
          setUpHelper(appLogicHook);
          appLogicHook.documents.loadAll = jest.fn();
          appLogicHook.benefitsApplications.isLoadingClaims = undefined;
        },
      },
      { query: { applicationWasSplitInto: "400" } }
    );

    const successPartOne = screen.queryByText(
      /You successfully submitted Part 1. Submit Parts 2 and 3 so that we can review your application./
    );
    const successPartOneAndTwo = screen.queryByText(
      "You successfully submitted Part 1. Your application was split into two, one for each benefit year. Submit Parts 2 and 3 so that we can review your applications."
    );

    expect(successPartOneAndTwo).not.toBeInTheDocument();
    expect(successPartOne).not.toBeInTheDocument();
  });

  it("displays prompt for channel switching", () => {
    renderPage(Index, {
      pathname: routes.applications.index,
      addCustomSetup: (appLogicHook) => {
        setUpHelper(appLogicHook);
      },
    });

    expect(
      screen.getByText("Did you start an application by phone?")
    ).toBeInTheDocument();
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
