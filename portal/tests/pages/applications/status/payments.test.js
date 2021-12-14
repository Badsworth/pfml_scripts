// TODO (PORTAL-1148) Update to use createMockClaim when ready
import ClaimDetail from "../../../../src/models/ClaimDetail";
import DocumentCollection from "../../../../src/models/DocumentCollection";
import { DocumentType } from "../../../../src/models/Document";
import { Payments } from "../../../../src/pages/applications/status/payments";
import { createMockPayment } from "../../../test-utils/createMockPayment";
import { mockRouter } from "next/router";
import { renderPage } from "../../../test-utils";
import routes from "../../../../src/routes";
import { screen } from "@testing-library/react";

jest.mock("next/router");

mockRouter.asPath = routes.applications.status.payments;

const renderWithApprovalNotice = (appLogicHook, isRetroactive = true) => {
  appLogicHook.documents.loadAll = jest.fn();
  appLogicHook.documents.documents = new DocumentCollection([
    {
      application_id: "mock-application-id",
      content_type: "image/png",
      created_at: isRetroactive ? "2022-12-30" : "2021-11-30",
      document_type: DocumentType.approvalNotice,
      fineos_document_id: "fineos-id-7",
      name: "legal notice 3",
    },
  ]);
  appLogicHook.documents.hasLoadedClaimDocuments = () => true;
};

const setupHelper = (claimDetailAttrs, isRetroactive) => (appLogicHook) => {
  appLogicHook.claims.claimDetail = claimDetailAttrs
    ? new ClaimDetail(claimDetailAttrs)
    : null;
  appLogicHook.claims.loadClaimDetail = jest.fn();
  renderWithApprovalNotice(appLogicHook, isRetroactive);
};

const defaultClaimDetail = {
  application_id: "mock-application-id",
  fineos_absence_id: "mock-absence-case-id",
  employer: { employer_fein: "12-1234567" },
  absence_periods: [
    {
      period_type: "Continuous",
      absence_period_start_date: "2021-10-21",
      absence_period_end_date: "2021-12-30",
      reason: "Child Bonding",
    },
  ],
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
            createMockPayment({ status: "Sent to bank" }, true),
            createMockPayment(
              { status: "Delayed", sent_to_bank_date: null },
              true
            ),
            createMockPayment(
              { status: "Pending", sent_to_bank_date: null },
              true
            ),
            createMockPayment({ status: "Sent to bank" }, true),
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
