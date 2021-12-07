// TODO (PORTAL-1148) Update to use createMockClaim when ready
import ClaimDetail from "../../../../src/models/ClaimDetail";
import { Payments } from "../../../../src/pages/applications/status/payments";
import { mockRouter } from "next/router";
import { renderPage } from "../../../test-utils";
import routes from "../../../../src/routes";
import { screen } from "@testing-library/react";

jest.mock("next/router");

mockRouter.asPath = routes.applications.status.payments;

const setupHelper = (claimDetailAttrs) => (appLogicHook) => {
  appLogicHook.claims.claimDetail = claimDetailAttrs
    ? new ClaimDetail(claimDetailAttrs)
    : null;
  appLogicHook.claims.loadClaimDetail = jest.fn();
};

const defaultClaimDetail = {
  application_id: "mock-application-id",
  fineos_absence_id: "mock-absence-case-id",
  employer: { employer_fein: "12-1234567" },
  payments: [],
};

const props = {
  query: {
    absence_id: defaultClaimDetail.fineos_absence_id,
  },
};

describe("Payments", () => {
  beforeEach(() => {
    process.env.featureFlags = {
      claimantShowPayments: true,
    };
  });

  it("redirects to status page if feature flag is not enabled", () => {
    process.env.featureFlags = {
      claimantShowPayments: false,
    };

    const goToSpy = jest.fn();
    renderPage(
      Payments,
      {
        addCustomSetup: (appLogicHook) => {
          appLogicHook.claims.loadClaimDetail = jest.fn();
          appLogicHook.portalFlow.goTo = goToSpy;
        },
      },
      props
    );

    expect(goToSpy).toHaveBeenCalledWith(routes.applications.status.claim, {
      absence_id: props.query.absence_id,
    });
  });

  it("renders the back button", () => {
    renderPage(
      Payments,
      { addCustomSetup: setupHelper(defaultClaimDetail) },
      props
    );

    const backButton = screen.getByRole("link", {
      name: /back to your applications/i,
    });

    expect(backButton).toBeInTheDocument();
  });

  it("renders the `changes to payments` section", () => {
    renderPage(
      Payments,
      { addCustomSetup: setupHelper(defaultClaimDetail) },
      props
    );

    const section = screen.getByTestId("changes-to-payments");
    expect(section).toMatchSnapshot();
  });

  it("renders the `help` section containing questions and feedback", () => {
    renderPage(
      Payments,
      { addCustomSetup: setupHelper(defaultClaimDetail) },
      props
    );

    const section = screen.getByTestId("helpSection");
    expect(section).toMatchSnapshot();

    const details = screen.getAllByText(/call the contact center at/i);
    expect(details.length).toBe(2);
  });

  it("renders the Payments table", () => {
    renderPage(
      Payments,
      {
        addCustomSetup: setupHelper({
          ...defaultClaimDetail,
          absence_periods: [
            {
              absence_period_start_date: "2021-10-21",
              absence_period_end_date: "2021-12-30",
              reason: "Child Bonding",
            },
          ],
          payments: [
            {
              payment_id: "1231",
              period_start_date: "2021-10-08",
              period_end_date: "2021-10-15",
              amount: 100,
              sent_to_bank_date: "2021-10-16",
              payment_method: "Check",
              expected_send_date_start: "2021-10-15",
              expected_send_date_end: "2021-10-21",
              status: "Sent to bank",
            },
            {
              payment_id: "1235",
              period_start_date: "2021-10-16",
              period_end_date: "2021-10-23",
              amount: null,
              sent_to_bank_date: null,
              payment_method: "Check",
              expected_send_date_start: null,
              expected_send_date_end: null,
              status: "Delayed",
            },
            {
              payment_id: "1235",
              period_start_date: "2021-11-08",
              period_end_date: "2021-11-15",
              amount: null,
              sent_to_bank_date: null,
              payment_method: "Check",
              expected_send_date_start: null,
              expected_send_date_end: null,
              status: "Pending",
            },
            {
              payment_id: "1234",
              period_start_date: "2021-10-31",
              period_end_date: "2021-11-07",
              amount: 100,
              sent_to_bank_date: "2021-11-08",
              payment_method: "Check",
              expected_send_date_start: "2021-11-08",
              expected_send_date_end: "2021-11-11",
              status: "Sent to bank",
            },
          ],
          appLogicHook: {
            claims: { loadClaimDetail: jest.fn() },
            appErrors: { items: [] },
          },
        }),
      },
      {
        ...props,
      }
    );

    const table = screen.getByRole("table");
    expect(table).toBeInTheDocument();
    expect(table.children.length).toBe(2);
    expect(table).toMatchSnapshot();
  });

  it("redirects to 404 if there's no absence case ID", () => {
    renderPage(
      Payments,
      {
        addCustomSetup: setupHelper(),
      },
      { query: {} }
    );

    const pageNotFoundHeading = screen.getByRole("heading", {
      name: /Page not found/,
    });
    expect(pageNotFoundHeading).toBeInTheDocument();
  });
});
