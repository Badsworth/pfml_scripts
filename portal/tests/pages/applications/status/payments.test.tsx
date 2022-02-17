import {
  BenefitsApplicationDocument,
  DocumentType,
} from "../../../../src/models/Document";
// TODO (PORTAL-1148) Update to use createMockClaim when ready
import { createAbsencePeriod, renderPage } from "../../../test-utils";
import ApiResourceCollection from "src/models/ApiResourceCollection";
import AppErrorInfo from "../../../../src/models/AppErrorInfo";
import { AppLogic } from "../../../../src/hooks/useAppLogic";
import ClaimDetail from "../../../../src/models/ClaimDetail";
import LeaveReason from "../../../../src/models/LeaveReason";
import { Payment } from "../../../../src/models/Payment";
import { Payments } from "../../../../src/pages/applications/status/payments";
import { createMockBenefitsApplicationDocument } from "../../../../lib/mock-helpers/createMockDocument";
import { createMockPayment } from "lib/mock-helpers/createMockPayment";
import dayjs from "dayjs";
import routes from "../../../../src/routes";
import { screen } from "@testing-library/react";

const renderWithApprovalNotice = (
  appLogicHook: AppLogic,
  isRetroactive = true,
  approvalTime = ""
) => {
  appLogicHook.documents.documents =
    new ApiResourceCollection<BenefitsApplicationDocument>(
      "fineos_document_id",
      [
        createMockBenefitsApplicationDocument({
          application_id: "mock-application-id",
          content_type: "image/png",
          created_at: isRetroactive ? "2021-11-30" : approvalTime,
          document_type: DocumentType.approvalNotice,
          fineos_document_id: "fineos-id-7",
          name: "legal notice 3",
        }),
      ]
    );
};

let goToSpy: jest.SpyInstance;

const setupHelper =
  (
    claimDetailAttrs?: Partial<ClaimDetail>,
    payments?: Partial<Payment>,
    isRetroactive?: boolean,
    approvalTime?: string,
    includeApprovalNotice = true
  ) =>
  (appLogicHook: AppLogic) => {
    appLogicHook.claims.claimDetail = claimDetailAttrs
      ? new ClaimDetail(claimDetailAttrs)
      : undefined;
    appLogicHook.claims.loadClaimDetail = jest.fn();
    goToSpy = jest.spyOn(appLogicHook.portalFlow, "goTo");
    appLogicHook.appErrors = [];
    appLogicHook.documents.loadAll = jest.fn();
    appLogicHook.documents.hasLoadedClaimDocuments = () => true;
    if (includeApprovalNotice) {
      renderWithApprovalNotice(appLogicHook, isRetroactive, approvalTime);
    }
    appLogicHook.payments.loadPayments = jest.fn();
    appLogicHook.payments.loadedPaymentsData = payments
      ? new Payment(payments)
      : new Payment();
    appLogicHook.payments.hasLoadedPayments = () => true;
  };

const defaultClaimDetail = new ClaimDetail({
  application_id: "mock-application-id",
  fineos_absence_id: "mock-absence-case-id",
  employer: {
    employer_fein: "12-1234567",
    employer_dba: "Acme",
    employer_id: "mock-employer-id",
  },
  absence_periods: [
    createAbsencePeriod({
      period_type: "Continuous",
      absence_period_start_date: "2021-10-21",
      absence_period_end_date: "2021-12-30",
      reason: "Child Bonding",
      request_decision: "Approved",
    }),
  ],
});

const approvalDate = {
  "approved after fourteenth claim date": dayjs(
    defaultClaimDetail.absence_periods[0].absence_period_start_date
  )
    .add(14, "day")
    .format("YYYY-MM-DD"),
  "approved before fourteenth claim date": dayjs(
    defaultClaimDetail.absence_periods[0].absence_period_start_date
  )
    .subtract(14, "day")
    .format("YYYY-MM-DD"),
  "with retroactive claim date": dayjs(
    defaultClaimDetail.absence_periods[0].absence_period_end_date
  )
    .add(14, "day")
    .format("YYYY-MM-DD"),
};

const props = {
  query: {
    absence_id: defaultClaimDetail.fineos_absence_id,
  },
};

describe("Payments", () => {
  it("redirects to status page if feature flag is not enabled and claim has loaded", () => {
    process.env.featureFlags = JSON.stringify({
      claimantShowPaymentsPhaseTwo: false,
    });
    renderPage(
      Payments,
      {
        addCustomSetup: setupHelper(defaultClaimDetail, {
          payments: [
            createMockPayment({ status: "Sent to bank" }, true),
            createMockPayment(
              { status: "Delayed", sent_to_bank_date: null },
              true
            ),
          ],
        }),
      },
      props
    );

    expect(goToSpy).toHaveBeenCalledWith(routes.applications.status.claim, {
      absence_id: props.query.absence_id,
    });
  });

  it("redirects to status page if claim does not have an approval notice", () => {
    process.env.featureFlags = JSON.stringify({
      claimantShowPaymentsPhaseTwo: true,
    });

    renderPage(
      Payments,
      {
        addCustomSetup: setupHelper(
          defaultClaimDetail,
          {}, // default
          true, // default
          "", // default
          false // Dont render the approval notice
        ),
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
            createAbsencePeriod({
              period_type: "Reduced Schedule",
              reason: LeaveReason.bonding,
              request_decision: "Pending",
              reason_qualifier_one: "Newborn",
            }),
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
            createAbsencePeriod({
              period_type: "Reduced Schedule",
              reason: LeaveReason.pregnancy,
              request_decision: "Approved",
            }),
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
            createAbsencePeriod({
              period_type: "Reduced Schedule",
              reason: LeaveReason.pregnancy,
              request_decision: "Approved",
            }),
            createAbsencePeriod({
              period_type: "Reduced Schedule",
              reason: LeaveReason.bonding,
              request_decision: "Approved",
            }),
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
            createAbsencePeriod({
              period_type: "Reduced Schedule",
              absence_period_start_date: "2022-10-21",
              absence_period_end_date: "2022-12-30",
              reason: "Child Bonding",
            }),
          ],
        }),
      },
      props
    );

    expect(
      screen.queryByText(/receive one payment for your entire leave/)
    ).not.toBeInTheDocument();
    expect(screen.getByText(/Check back weekly/)).toBeInTheDocument();
  });

  it("renders retroactive text if latest absence period date is retroactive", () => {
    renderPage(
      Payments,
      {
        addCustomSetup: setupHelper({
          ...defaultClaimDetail,
          absence_periods: [
            createAbsencePeriod({
              period_type: "Reduced Schedule",
              absence_period_start_date: "2021-07-21",
              absence_period_end_date: "2021-18-30",
              reason: "Child Bonding",
            }),
            createAbsencePeriod({
              period_type: "Reduced Schedule",
              absence_period_start_date: "2021-09-21",
              absence_period_end_date: "2021-10-30",
              reason: "Child Bonding",
            }),
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
        addCustomSetup: setupHelper(
          {
            ...defaultClaimDetail,
          },
          {
            absence_case_id: "NTN-12345-ABS-01",
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
          }
        ),
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
          appErrors: [
            new AppErrorInfo({
              meta: { application_id: "foo" },
              key: "AppErrorInfo1",
              message:
                "Sorry, we were unable to retrieve what you were looking for. Check that the link you are visiting is correct. If this continues to happen, please log out and try again.",
              name: "NotFoundError",
            }),
          ],
          documents: {
            documents: new ApiResourceCollection<BenefitsApplicationDocument>(
              "fineos_document_id",
              []
            ),
            loadAll: { loadAllClaimDocuments: jest.fn() },
          },
          payments: {
            loadPayments: jest.fn(),
            loadedPaymentsData: [],
            hasLoadedPayments: jest.fn,
            isLoadingPayments: false,
          },
        },
      }
    );

    expect(screen.queryByText(/Payments/)).not.toBeInTheDocument();
    expect(container.firstChild).toMatchSnapshot();
  });

  // TODO(PORTAL-1482): remove test cases for checkback dates
  describe("Phase 2 Checkback date implementation", () => {
    beforeEach(() => {
      process.env.featureFlags = JSON.stringify({
        claimantShowPaymentsPhaseTwo: true,
      });
    });

    it("does not render checkback dates for claims that have at least one payment row", () => {
      renderPage(
        Payments,
        {
          addCustomSetup: setupHelper(
            {
              ...defaultClaimDetail,
            },
            {
              absence_case_id: "NTN-12345-ABS-01",
              payments: [
                createMockPayment(
                  { status: "Delayed", sent_to_bank_date: null },
                  true
                ),
              ],
            }
          ),
        },
        props
      );

      expect(screen.queryByText(/Check back on/)).not.toBeInTheDocument();
      expect(screen.getByTestId("your-payments-intro")).toMatchSnapshot();
    });

    it.each(Object.keys(approvalDate) as Array<keyof typeof approvalDate>)(
      "renders intro text for continuous leaves %s ",
      (state) => {
        renderPage(
          Payments,
          {
            addCustomSetup: setupHelper(
              {
                ...defaultClaimDetail,
              },
              {},
              false,
              approvalDate[state]
            ),
          },
          props
        );
        const table = screen.getByRole("table");
        expect(table).toBeInTheDocument();
        expect(screen.getByTestId("your-payments-intro")).toMatchSnapshot();
      }
    );

    it.each(Object.keys(approvalDate) as Array<keyof typeof approvalDate>)(
      "renders intro text for reduced schedule leaves %s ",
      (state) => {
        const reducedClaimDetail = new ClaimDetail({
          ...defaultClaimDetail,
          absence_periods: [
            {
              ...defaultClaimDetail.absence_periods[0],
              period_type: "Reduced Schedule",
            },
          ],
        });
        renderPage(
          Payments,
          {
            addCustomSetup: setupHelper(
              {
                ...reducedClaimDetail,
              },
              {},
              false,
              approvalDate[state]
            ),
          },
          props
        );
        expect(screen.getByTestId("your-payments-intro")).toMatchSnapshot();
        const table = screen.getByRole("table");
        expect(table).toBeInTheDocument();
      }
    );

    it.each(Object.keys(approvalDate) as Array<keyof typeof approvalDate>)(
      "renders intro text for continous leaves %s if claim has reduced and continuous leaves",
      (state) => {
        const multipleClaimDetail = new ClaimDetail({
          ...defaultClaimDetail,
          absence_periods: [
            defaultClaimDetail.absence_periods[0],
            {
              ...defaultClaimDetail.absence_periods[0],
              period_type: "Reduced Schedule",
            },
          ],
        });
        renderPage(
          Payments,
          {
            addCustomSetup: setupHelper(
              {
                ...multipleClaimDetail,
              },
              {},
              false,
              approvalDate[state]
            ),
          },
          props
        );
        expect(screen.getByTestId("your-payments-intro")).toMatchSnapshot();
        const table = screen.getByRole("table");
        expect(table).toBeInTheDocument();
      }
    );

    it("does not render the Payments table when no payments are available and leave is intermittent", () => {
      renderPage(
        Payments,
        {
          addCustomSetup: setupHelper({
            ...defaultClaimDetail,
            absence_periods: [
              defaultClaimDetail.absence_periods[0],
              {
                ...defaultClaimDetail.absence_periods[0],
                period_type: "Intermittent",
              },
            ],
          }),
        },
        {
          ...props,
        }
      );

      expect(screen.getByTestId("your-payments-intro")).toMatchSnapshot();
      const table = screen.queryByRole("table");
      expect(table).not.toBeInTheDocument();
    });
  });
});
