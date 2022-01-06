// TODO (PORTAL-1148) Update to use createMockClaim when ready
import AppErrorInfo from "../../../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../../../src/models/AppErrorInfoCollection";
import ClaimDetail from "../../../../src/models/ClaimDetail";
import DocumentCollection from "../../../../src/models/DocumentCollection";
import { DocumentType } from "../../../../src/models/Document";
import LeaveReason from "../../../../src/models/LeaveReason";
import { Payments } from "../../../../src/pages/applications/status/payments";
import { createMockPayment } from "lib/mock-helpers/createMockPayment";
import { mockRouter } from "next/router";
import { renderPage } from "../../../test-utils";
import routes from "../../../../src/routes";
import { screen } from "@testing-library/react";

jest.mock("next/router");

mockRouter.asPath = routes.applications.status.payments;

const renderWithApprovalNotice = (appLogicHook, isRetroactive = true) => {
  appLogicHook.appErrors = new AppErrorInfoCollection();
  appLogicHook.documents.loadAll = jest.fn();
  appLogicHook.documents.documents = new DocumentCollection([
    {
      application_id: "mock-application-id",
      content_type: "image/png",
      created_at: isRetroactive ? "2021-11-30" : "2022-12-30",
      document_type: DocumentType.approvalNotice,
      fineos_document_id: "fineos-id-7",
      name: "legal notice 3",
    },
  ]);
  appLogicHook.documents.hasLoadedClaimDocuments = () => true;
};

let goToSpy;

const setupHelper = (claimDetailAttrs, isRetroactive) => (appLogicHook) => {
  appLogicHook.claims.claimDetail =
    claimDetailAttrs && new ClaimDetail(claimDetailAttrs);
  appLogicHook.claims.loadClaimDetail = jest.fn();
  goToSpy = jest.spyOn(appLogicHook.portalFlow, "goTo");
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

  it("redirects to status page if feature flag is not enabled and claim has loaded", () => {
    process.env.featureFlags = {
      claimantShowPayments: false,
      claimantShowPaymentsPhaseTwo: false,
    };

    renderPage(
      Payments,
      {
        addCustomSetup: setupHelper({
          ...defaultClaimDetail,
        }),
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

  it("displays info alert if claimant has bonding-newborn but not pregnancy claims", () => {
    renderPage(
      Payments,
      {
        addCustomSetup: setupHelper({
          ...defaultClaimDetail,
          absence_periods: [
            {
              period_type: "Reduced",
              reason: LeaveReason.bonding,
              request_decision: "Pending",
              reason_qualifier_one: "Newborn",
            },
          ],
        }),
      },
      props
    );

    expect(screen.getByRole("region")).toMatchSnapshot();
  });

  it("displays info alert if claimant has pregnancy but not bonding claims", () => {
    renderPage(
      Payments,
      {
        addCustomSetup: setupHelper({
          ...defaultClaimDetail,
          absence_periods: [
            {
              period_type: "Reduced",
              reason: LeaveReason.pregnancy,
              request_decision: "Approved",
            },
          ],
        }),
      },
      props
    );

    expect(screen.getByRole("region")).toMatchSnapshot();
  });

  it("does not display info alert if claimant has bonding AND pregnancy claims", () => {
    renderPage(
      Payments,
      {
        addCustomSetup: setupHelper({
          ...defaultClaimDetail,
          absence_periods: [
            {
              period_type: "Reduced",
              reason: LeaveReason.pregnancy,
              request_decision: "Approved",
            },
            {
              period_type: "Reduced",
              reason: LeaveReason.bonding,
              request_decision: "Approved",
            },
          ],
        }),
      },
      props
    );
    expect(screen.queryByRole("region")).not.toBeInTheDocument();
  });

  it("renders the `Your payments` intro content section", () => {
    renderPage(
      Payments,
      { addCustomSetup: setupHelper(defaultClaimDetail) },
      props
    );

    const section = screen.getByTestId("your-payments-intro");
    expect(section).toMatchSnapshot();
  });

  it("renders non-retroactive text if latest absence period date is not retroactive", () => {
    renderPage(
      Payments,
      {
        addCustomSetup: setupHelper({
          ...defaultClaimDetail,
          absence_periods: [
            ...defaultClaimDetail.absence_periods,
            {
              period_type: "Reduced",
              absence_period_start_date: "2022-10-21",
              absence_period_end_date: "2022-12-30",
              reason: "Child Bonding",
            },
          ],
        }),
      },
      props
    );

    expect(
      screen.queryByText(/receive one payment for your entire leave/)
    ).not.toBeInTheDocument();
    expect(
      screen.getByText(
        /expect to be paid weekly for the duration of your leave/
      )
    ).toBeInTheDocument();
  });

  it("renders retroactive text if latest absence period date is retroactive", () => {
    renderPage(
      Payments,
      {
        addCustomSetup: setupHelper({
          ...defaultClaimDetail,
          absence_periods: [
            {
              period_type: "Reduced",
              absence_period_start_date: "2021-07-21",
              absence_period_end_date: "2021-18-30",
              reason: "Child Bonding",
            },
            {
              period_type: "Reduced",
              absence_period_start_date: "2021-09-21",
              absence_period_end_date: "2021-10-30",
              reason: "Child Bonding",
            },
          ],
        }),
      },
      props
    );

    expect(
      screen.getByText(/receive one payment for your entire leave/)
    ).toBeInTheDocument();
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
          loadedPaymentsData: {
            absence_case_id: "fineos_id",
          },
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

  it("displays page not found alert if there's no absence case ID", () => {
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

  it("does not render payments if the is a 404 status", () => {
    const { container } = renderPage(
      Payments,
      {
        addCustomSetup: setupHelper(),
      },
      {
        query: { absence_id: "foo" },
        appLogic: {
          claims: {
            loadClaimDetail: jest.fn(),
            claimDetail: undefined,
            isLoadingClaimDetail: false,
          },
          appErrors: new AppErrorInfoCollection([
            new AppErrorInfo({
              meta: { application_id: "foo" },
              key: "AppErrorInfo1",
              message:
                "Sorry, we were unable to retrieve what you were looking for. Check that the link you are visiting is correct. If this continues to happen, please log out and try again.",
              name: "NotFoundError",
            }),
          ]),

          documents: {
            documents: null,
            loadAll: { loadAllClaimDocuments: jest.fn() },
          },
        },
      }
    );

    expect(screen.queryByText(/Payments/)).not.toBeInTheDocument();
    expect(container.firstChild).toMatchSnapshot();
  });
});