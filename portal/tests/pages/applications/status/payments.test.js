// TODO (PORTAL-1148) Update to use createMockClaim when ready
import ClaimDetail from "../../../../src/models/ClaimDetail";
import { Payments } from "../../../../src/pages/applications/status/payments";
import { createMockPayment } from "../../../test-utils/createMockPayment";
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
          payments: [
            createMockPayment("Pending", "Check", true),
            createMockPayment("Sent to bank", "Check", true),
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

  it("renders pending payment data when payment is yet to be made", () => {
    renderPage(
      Payments,
      {
        addCustomSetup: setupHelper({
          ...defaultClaimDetail,
          payments: [],
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

    const paymentPendingInfo = screen.getByTestId("payment-pending-info");
    expect(paymentPendingInfo).toBeInTheDocument();
  });

  it("does not render pending payment data when payment is already made", () => {
    renderPage(
      Payments,
      {
        addCustomSetup: setupHelper({
          ...defaultClaimDetail,
          payments: [
            createMockPayment("Pending", "Check", true),
            createMockPayment("Sent to bank", "Check", true),
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

    const paymentPendingInfo = screen.queryByTestId("payment-pending-info");
    expect(paymentPendingInfo).not.toBeInTheDocument();
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
