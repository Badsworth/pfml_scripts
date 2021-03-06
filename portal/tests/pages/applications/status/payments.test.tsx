import {
  BenefitsApplicationDocument,
  DocumentType,
} from "../../../../src/models/Document";
import {
  PROCESSING_DAYS_PER_DELAY,
  Payment,
} from "../../../../src/models/Payment";
// TODO (PORTAL-1148) Update to use createMockClaim when ready
import { createAbsencePeriod, renderPage } from "../../../test-utils";
import { AbsencePeriod } from "../../../../src/models/AbsencePeriod";
import ApiResourceCollection from "src/models/ApiResourceCollection";
import { AppLogic } from "../../../../src/hooks/useAppLogic";
import ClaimDetail from "../../../../src/models/ClaimDetail";
import { Holiday } from "../../../../src/models/Holiday";
import LeaveReason from "../../../../src/models/LeaveReason";
import { NotFoundError } from "../../../../src/errors";
import Payments from "../../../../src/pages/applications/status/payments";
import { createMockBenefitsApplicationDocument } from "../../../../lib/mock-helpers/createMockDocument";
import { createMockPayment } from "lib/mock-helpers/createMockPayment";
import dayjs from "dayjs";
import dayjsBusinessTime from "dayjs-business-time";
import routes from "../../../../src/routes";
import { screen } from "@testing-library/react";

dayjs.extend(dayjsBusinessTime);

const createApprovalNotice = (approvalDate: string) => {
  return new ApiResourceCollection<BenefitsApplicationDocument>(
    "fineos_document_id",
    [
      createMockBenefitsApplicationDocument({
        created_at: approvalDate,
        document_type: DocumentType.approvalNotice,
      }),
    ]
  );
};

interface SetupOptions {
  absence_periods?: AbsencePeriod[];
  payments?: Partial<Payment>;
  goTo?: jest.Mock;
  approvalDate?: string;
  includeApprovalNotice?: boolean;
  holidays?: Holiday[];
  useDefaultClaim?: boolean;
  errors?: Error[];
}

const setupHelper =
  ({
    absence_periods = [defaultAbsencePeriod],
    payments = new Payment(),
    goTo = jest.fn(),
    approvalDate = defaultApprovalDate.format("YYYY-MM-DD"),
    includeApprovalNotice = false,
    holidays = defaultHolidays,
    useDefaultClaim = true,
    errors = [],
  }: SetupOptions) =>
  (appLogicHook: AppLogic) => {
    appLogicHook.claims.claimDetail = useDefaultClaim
      ? new ClaimDetail({
          ...defaultClaimDetailAttributes,
          absence_periods,
        })
      : undefined;
    appLogicHook.claims.loadClaimDetail = jest.fn();
    appLogicHook.errors = errors;
    appLogicHook.documents.loadAll = jest.fn();
    appLogicHook.documents.hasLoadedClaimDocuments = () => true;
    appLogicHook.holidays.holidays = holidays;
    appLogicHook.holidays.loadHolidays = jest.fn();
    appLogicHook.holidays.hasLoadedHolidays = true;
    appLogicHook.holidays.isLoadingHolidays = false;
    appLogicHook.portalFlow.goTo = goTo;
    if (includeApprovalNotice) {
      appLogicHook.documents.documents = createApprovalNotice(approvalDate);
    }
    appLogicHook.payments.loadPayments = jest.fn();
    appLogicHook.payments.loadedPaymentsData = new Payment(payments);
    appLogicHook.payments.hasLoadedPayments = () => true;
  };

// Extracted from setupHelper arguments because abscence_period_start_date (and end)
// should be based on this in future work.
const defaultApprovalDate = dayjs().add(-3, "months");

const defaultAbsencePeriod = createAbsencePeriod({
  period_type: "Continuous",
  absence_period_start_date: "2021-10-21",
  absence_period_end_date: "2021-12-30",
  reason: "Child Bonding",
  request_decision: "Approved",
});

const defaultClaimDetailAttributes = {
  application_id: "mock-application-id",
  fineos_absence_id: "mock-absence-case-id",
  employer: {
    employer_fein: "12-1234567",
    employer_dba: "Acme",
    employer_id: "mock-employer-id",
  },
  absence_periods: [defaultAbsencePeriod],
};

const defaultHolidays = [{ name: "Memorial Day", date: "2022-05-30" }];
const defaultHolidayAlertText =
  "Due to the upcoming holiday, payments may be delayed by one business day.";

const props = {
  query: {
    absence_id: defaultClaimDetailAttributes.fineos_absence_id,
  },
};

describe("Payments", () => {
  it("redirects to status page if claim is not approved and has no payments", () => {
    const goToMock = jest.fn();

    renderPage(
      Payments,
      {
        // includeApprovalNotice is false by default in setupHelper, passing for clarity
        addCustomSetup: setupHelper({
          absence_periods: [
            { ...defaultAbsencePeriod, request_decision: "Pending" },
          ],
          goTo: goToMock,
          includeApprovalNotice: false,
        }),
      },
      props
    );

    expect(goToMock).toHaveBeenCalledWith(routes.applications.status.claim, {
      absence_id: props.query.absence_id,
    });
  });

  it("renders the back button", () => {
    renderPage(Payments, { addCustomSetup: setupHelper({}) }, props);

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

    const bondingAlertText =
      "If you are giving birth, you may also be eligible for paid medical leave";
    expect(
      screen.getByText(bondingAlertText, { exact: false })
    ).toBeInTheDocument();
  });

  it("displays info alert if claimant has pregnancy but not bonding claims", () => {
    renderPage(
      Payments,
      {
        addCustomSetup: setupHelper({
          absence_periods: [
            createAbsencePeriod({
              period_type: "Reduced Schedule",
              reason: LeaveReason.pregnancy,
              request_decision: "Approved",
            }),
          ],
          includeApprovalNotice: true,
        }),
      },
      props
    );

    const pregnancyAlertText =
      "You may be able to take up to 12 weeks of paid family leave to bond with your child after your medical leave ends.";
    expect(
      screen.getByText(pregnancyAlertText, { exact: false })
    ).toBeInTheDocument();
  });

  it("does not display info alert if claimant has bonding AND pregnancy claims", () => {
    renderPage(
      Payments,
      {
        addCustomSetup: setupHelper({
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
          includeApprovalNotice: true,
        }),
      },
      props
    );
    const bondingAlertText =
      "If you are giving birth, you may also be eligible for paid medical leave";
    const pregnancyAlertText =
      "You may be able to take up to 12 weeks of paid family leave to bond with your child after your medical leave ends.";
    expect(
      screen.queryByText(bondingAlertText, { exact: false })
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText(pregnancyAlertText, { exact: false })
    ).not.toBeInTheDocument();
  });

  it("doesn't show the holiday alert when there are holidays, but the claimantShowPaymentsPhaseThree feature flag is off", () => {
    process.env.featureFlags = JSON.stringify({
      showHolidayAlert: true,
      claimantShowPaymentsPhaseThree: false,
    });
    renderPage(Payments, { addCustomSetup: setupHelper({}) }, props);
    expect(screen.queryByText(defaultHolidayAlertText)).not.toBeInTheDocument();
  });

  it("doesn't show the holiday alert when there are holidays, but the holiday alert feature flag is off", () => {
    process.env.featureFlags = JSON.stringify({
      showHolidayAlert: false,
      claimantShowPaymentsPhaseThree: true,
    });
    renderPage(Payments, { addCustomSetup: setupHelper({}) }, props);
    expect(screen.queryByText(defaultHolidayAlertText)).not.toBeInTheDocument();
  });

  it("doesn't show the holiday alert when there are no holidays", () => {
    process.env.featureFlags = JSON.stringify({
      showHolidayAlert: true,
      claimantShowPaymentsPhaseThree: true,
    });
    renderPage(
      Payments,
      { addCustomSetup: setupHelper({ holidays: [] }) },
      props
    );
    expect(screen.queryByText(defaultHolidayAlertText)).not.toBeInTheDocument();
  });

  it("shows the holiday alert when there are holidays", () => {
    process.env.featureFlags = JSON.stringify({
      showHolidayAlert: true,
      claimantShowPaymentsPhaseThree: true,
    });
    renderPage(Payments, { addCustomSetup: setupHelper({}) }, props);
    expect(screen.queryByText(defaultHolidayAlertText)).toBeInTheDocument();
  });

  it("renders the `Your payments` intro content section", () => {
    renderPage(Payments, { addCustomSetup: setupHelper({}) }, props);

    const section = screen.getByTestId("your-payments-intro");
    expect(section).toMatchSnapshot();
  });

  it("renders non-retroactive text if latest absence period date is in the future (not retroactive)", () => {
    renderPage(
      Payments,
      {
        addCustomSetup: setupHelper({
          absence_periods: [
            defaultAbsencePeriod,
            createAbsencePeriod({
              period_type: "Reduced Schedule",
              absence_period_start_date: dayjs()
                .add(2, "weeks")
                .format("YYYY-MM-DD"),
              absence_period_end_date: dayjs()
                .add(2, "weeks")
                .add(4, "months")
                .format("YYYY-MM-DD"),
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

  it("renders retroactive text if latest absence period date is in the past (retroactive)", () => {
    renderPage(
      Payments,
      {
        addCustomSetup: setupHelper({
          includeApprovalNotice: true,
          absence_periods: [
            createAbsencePeriod({
              period_type: "Reduced Schedule",
              absence_period_start_date: dayjs()
                .add(-8, "months")
                .format("YYYY-MM-DD"),
              absence_period_end_date: dayjs()
                .add(-8, "months")
                .add(1, "months")
                .format("YYYY-MM-DD"),
              reason: "Child Bonding",
            }),
            createAbsencePeriod({
              period_type: "Reduced Schedule",
              absence_period_start_date: dayjs()
                .add(-6, "months")
                .format("YYYY-MM-DD"),
              absence_period_end_date: dayjs()
                .add(-6, "months")
                .add(1, "months")
                .format("YYYY-MM-DD"),
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
    renderPage(Payments, { addCustomSetup: setupHelper({}) }, props);

    const section = screen.getByTestId("changes-to-payments");
    expect(section).toMatchSnapshot();
  });

  it("renders the `help` section containing questions and feedback", () => {
    renderPage(Payments, { addCustomSetup: setupHelper({}) }, props);

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
          payments: {
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

  it("shows a spinner if there is no claim detail", () => {
    renderPage(
      Payments,
      {
        addCustomSetup: setupHelper({
          useDefaultClaim: false,
        }),
      },
      props
    );
    expect(screen.getByRole("progressbar")).toBeInTheDocument();
  });

  it("displays page not found alert if there's no absence case ID", () => {
    renderPage(
      Payments,
      {
        addCustomSetup: setupHelper({ useDefaultClaim: false }),
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
        addCustomSetup: setupHelper({ errors: [new NotFoundError()] }),
      },
      props
    );

    expect(screen.queryByText(/Payments/)).not.toBeInTheDocument();
    expect(container.firstChild).toMatchSnapshot();
  });

  // TODO(PORTAL-1482): remove test cases for checkback dates
  describe("Checkback date implementation", () => {
    const approvalDate = {
      "approved before claim start date": dayjs(
        defaultAbsencePeriod.absence_period_start_date
      )
        .add(-1, "day")
        .format("YYYY-MM-DD"),
      "approved after fourteenth claim date": dayjs(
        defaultAbsencePeriod.absence_period_start_date
      )
        .add(14, "day")
        .format("YYYY-MM-DD"),
      "approved before fourteenth claim date": dayjs(
        defaultAbsencePeriod.absence_period_start_date
      )
        .add(7, "day")
        .format("YYYY-MM-DD"),
      "with retroactive claim date": dayjs(
        defaultAbsencePeriod.absence_period_end_date
      )
        .add(14, "day")
        .format("YYYY-MM-DD"),
    };
    const approvalDateScenarios = Object.keys(approvalDate) as Array<
      keyof typeof approvalDate
    >;

    it("does not render checkback dates for claims that have at least one payment row", () => {
      renderPage(
        Payments,
        {
          addCustomSetup: setupHelper({
            ...defaultClaimDetailAttributes,
            payments: {
              absence_case_id: "NTN-12345-ABS-01",
              payments: [
                createMockPayment(
                  { status: "Delayed", sent_to_bank_date: null },
                  true
                ),
              ],
            },
          }),
        },
        props
      );

      expect(screen.queryByText(/Check back on/)).not.toBeInTheDocument();
      expect(screen.getByTestId("your-payments-intro")).toMatchSnapshot();
    });

    it.each(approvalDateScenarios)(
      "renders intro text for continuous leaves %s ",
      (state) => {
        renderPage(
          Payments,
          {
            addCustomSetup: setupHelper({
              approvalDate: approvalDate[state],
              includeApprovalNotice: true,
            }),
          },
          props
        );
        const table = screen.getByRole("table");
        expect(table).toBeInTheDocument();
        expect(screen.getByTestId("your-payments-intro")).toMatchSnapshot();
      }
    );

    it.each(approvalDateScenarios)(
      "renders intro text for reduced schedule leaves %s ",
      (state) => {
        renderPage(
          Payments,
          {
            addCustomSetup: setupHelper({
              approvalDate: approvalDate[state],
              includeApprovalNotice: true,
              absence_periods: [
                {
                  ...defaultAbsencePeriod,
                  period_type: "Reduced Schedule",
                },
              ],
            }),
          },
          props
        );
        expect(screen.getByTestId("your-payments-intro")).toMatchSnapshot();
        const table = screen.getByRole("table");
        expect(table).toBeInTheDocument();
      }
    );

    it.each(approvalDateScenarios)(
      "renders intro text for continous leaves %s if claim has reduced and continuous leaves",
      (state) => {
        const reducedAbsencePeriod: AbsencePeriod = {
          ...defaultAbsencePeriod,
          period_type: "Reduced Schedule",
        };
        renderPage(
          Payments,
          {
            addCustomSetup: setupHelper({
              approvalDate: approvalDate[state],
              includeApprovalNotice: true,
              absence_periods: [defaultAbsencePeriod, reducedAbsencePeriod],
            }),
          },
          props
        );
        expect(screen.getByTestId("your-payments-intro")).toMatchSnapshot();
        const table = screen.getByRole("table");
        expect(table).toBeInTheDocument();
      }
    );

    it("does not render the Payments table when no payments are available and leave is intermittent", () => {
      const intermittenAbsencePeriod: AbsencePeriod = {
        ...defaultAbsencePeriod,
        period_type: "Intermittent",
      };
      renderPage(
        Payments,
        {
          addCustomSetup: setupHelper({
            absence_periods: [defaultAbsencePeriod, intermittenAbsencePeriod],
          }),
        },
        {
          ...props,
        }
      );

      const intermittentUnpaidIntroText =
        "Your application has an unpaid 7-day waiting period that begins the first day you report taking leave";
      expect(
        screen.getByText(intermittentUnpaidIntroText, { exact: false })
      ).toBeInTheDocument();
      expect(screen.getByTestId("your-payments-intro")).toMatchSnapshot();
      const table = screen.queryByRole("table");
      expect(table).not.toBeInTheDocument();
    });
  });

  describe("Phase Three: Status render implementation", () => {
    beforeEach(() => {
      process.env.featureFlags = JSON.stringify({
        claimantShowPaymentsPhaseThree: true,
      });
    });

    const staticTransactionDate = dayjs().format("YYYY-MM-DD");
    // transaction date to be compared with current date, current date
    const transactionDate = {
      "five business days before today": dayjs(staticTransactionDate)
        .subtractBusinessDays(5)
        .format("YYYY-MM-DD"),
      "four business days before today": dayjs(staticTransactionDate)
        .subtractBusinessDays(4)
        .format("YYYY-MM-DD"),
      "three business days before today": dayjs(staticTransactionDate)
        .subtractBusinessDays(3)
        .format("YYYY-MM-DD"),
      "two business days before today": dayjs(staticTransactionDate)
        .subtractBusinessDays(2)
        .format("YYYY-MM-DD"),
      "same day": staticTransactionDate,
    };

    const transactionDateScenarios = Object.keys(
      transactionDate
    ).sort() as Array<keyof typeof transactionDate>;

    it.each(transactionDateScenarios)(
      "conditional render for 'Bank Processing Error' writeback status with immediate display time: %s ",
      (state) => {
        renderPage(
          Payments,
          {
            addCustomSetup: setupHelper({
              payments: {
                absence_case_id: "NTN-12345-ABS-01",
                payments: [
                  createMockPayment(
                    {
                      status: "Delayed",
                      sent_to_bank_date: null,
                      writeback_transaction_status: "Bank Processing Error",
                      transaction_date: transactionDate[state],
                    },
                    true
                  ),
                ],
              },
            }),
          },
          props
        );

        const rejectedDelayReasonText =
          "This payment has been rejected by your bank.";
        expect(
          screen.queryByText(rejectedDelayReasonText, { exact: false })
        ).toBeInTheDocument();
      }
    );

    const [
      beforeFiveDays,
      beforeFourDays,
      sameDay,
      beforeThreeDays,
      beforeTwoDays,
    ] = transactionDateScenarios;

    it.each([beforeTwoDays, sameDay])(
      "conditional render for 'Address Validation Error' transaction status, shows 'Pending' status if current date has transaction date: %s ",
      (state) => {
        renderPage(
          Payments,
          {
            addCustomSetup: setupHelper({
              payments: {
                absence_case_id: "NTN-12345-ABS-01",
                payments: [
                  createMockPayment(
                    {
                      status: "Delayed",
                      sent_to_bank_date: null,
                      writeback_transaction_status: "Address Validation Error",
                      transaction_date: transactionDate[state],
                    },
                    true
                  ),
                ],
              },
            }),
          },
          props
        );

        const addressDelayReasonText =
          "This payment is delayed due to an error with your provided mailing address.";
        expect(
          screen.queryByText(addressDelayReasonText, { exact: false })
        ).not.toBeInTheDocument();
        expect(screen.queryByText("Delayed")).not.toBeInTheDocument();
        expect(screen.queryByText("Processing")).toBeInTheDocument();
      }
    );

    it.each([beforeThreeDays, beforeFourDays, beforeFiveDays])(
      "conditional render for 'Address Validation Error' transaction status, shows 'Delayed' status if current date has transaction date: %s ",
      (state) => {
        renderPage(
          Payments,
          {
            addCustomSetup: setupHelper({
              payments: {
                absence_case_id: "NTN-12345-ABS-01",
                payments: [
                  createMockPayment(
                    {
                      status: "Delayed",
                      sent_to_bank_date: null,
                      writeback_transaction_status: "Address Validation Error",
                      transaction_date: transactionDate[state],
                    },
                    true
                  ),
                ],
              },
            }),
          },
          props
        );

        const addressDelayReasonText =
          "This payment is delayed due to an error with your provided mailing address.";
        expect(
          screen.queryByText(addressDelayReasonText, { exact: false })
        ).toBeInTheDocument();
        expect(screen.queryByText("Delayed")).toBeInTheDocument();
        expect(screen.queryByText("Processing")).not.toBeInTheDocument();
      }
    );

    it("default render for status not in PROCESSING_DAYS_PER_DELAY ('DUA Additional Income') displays 'Delayed' status if transaction date after 3 business days", () => {
      const transactionStatus = "DUA Additional Income";
      renderPage(
        Payments,
        {
          addCustomSetup: setupHelper({
            payments: {
              absence_case_id: "NTN-12345-ABS-01",
              payments: [
                createMockPayment(
                  {
                    status: "Delayed",
                    sent_to_bank_date: null,
                    writeback_transaction_status: transactionStatus,
                    transaction_date: transactionDate[beforeFourDays],
                  },
                  true
                ),
              ],
            },
          }),
        },
        props
      );
      const defaultDelayReasonText =
        "Most delays are resolved within 3 to 5 business days. The Contact Center will contact you if they require more information.";
      expect(PROCESSING_DAYS_PER_DELAY).not.toHaveProperty(transactionStatus);
      expect(
        screen.queryByText(defaultDelayReasonText, { exact: false })
      ).toBeInTheDocument();
      expect(screen.queryByText("Delayed")).toBeInTheDocument();
      expect(screen.queryByText("Processing")).not.toBeInTheDocument();
    });

    it("default render for status not in PROCESSING_DAYS_PER_DELAY ('DUA Additional Income') will display 'Processing' status if transaction date before 2 business days", () => {
      const transactionStatus = "DUA Additional Income";
      renderPage(
        Payments,
        {
          addCustomSetup: setupHelper({
            payments: {
              absence_case_id: "NTN-12345-ABS-01",
              payments: [
                createMockPayment(
                  {
                    status: "Delayed",
                    sent_to_bank_date: null,
                    writeback_transaction_status: transactionStatus,
                    transaction_date: transactionDate[beforeThreeDays],
                  },
                  true
                ),
              ],
            },
          }),
        },
        props
      );
      const defaultDelayReasonText =
        "Most delays are resolved within 3 to 5 business days. The Contact Center will contact you if they require more information.";
      expect(PROCESSING_DAYS_PER_DELAY).not.toHaveProperty(transactionStatus);
      expect(
        screen.queryByText(defaultDelayReasonText, { exact: false })
      ).not.toBeInTheDocument();
      expect(screen.queryByText("Delayed")).not.toBeInTheDocument();
      expect(screen.queryByText("Processing")).toBeInTheDocument();
    });

    it("renders generic processing text if transaction_date_could_change is true and expected_send_start_date/expected_send_end_date are null", () => {
      const transactionStatus = "Pending Payment Audit";
      renderPage(
        Payments,
        {
          addCustomSetup: setupHelper({
            payments: {
              absence_case_id: "NTN-12345-ABS-01",
              payments: [
                createMockPayment(
                  {
                    status: "Delayed",
                    sent_to_bank_date: null,
                    writeback_transaction_status: "Pending Payment Audit",
                    transaction_date: transactionDate[sameDay],
                    transaction_date_could_change: true,
                  },
                  true
                ),
              ],
            },
          }),
        },
        props
      );
      const transactionDateCouldChangeDelayReasonText =
        "dates will be available in a few days. No action is required from you at this time";
      expect(PROCESSING_DAYS_PER_DELAY).not.toHaveProperty(transactionStatus);
      expect(
        screen.queryByText(transactionDateCouldChangeDelayReasonText, {
          exact: false,
        })
      ).toBeInTheDocument();
      expect(screen.queryByText("Delayed")).not.toBeInTheDocument();
      expect(screen.queryByText("Processing")).toBeInTheDocument();
    });

    it("will not display updated delay text if claimantShowPaymentsPhaseThree feature flag is false", () => {
      process.env.featureFlags = JSON.stringify({
        claimantShowPaymentsPhaseThree: false,
      });
      renderPage(
        Payments,
        {
          addCustomSetup: setupHelper({
            payments: {
              absence_case_id: "NTN-12345-ABS-01",
              payments: [
                createMockPayment(
                  {
                    status: "Delayed",
                    sent_to_bank_date: null,
                    writeback_transaction_status: "Bank Processing Error",
                    transaction_date:
                      transactionDate["five business days before today"],
                  },
                  true
                ),
              ],
            },
          }),
        },
        props
      );

      const rejectedDelayReasonText =
        "This payment has been rejected by your bank.";
      expect(
        screen.queryByText(rejectedDelayReasonText, { exact: false })
      ).not.toBeInTheDocument();
    });
  });

  describe("Post FINEOS deploy checkback date updates", () => {
    beforeEach(() => {
      process.env.featureFlags = JSON.stringify({
        claimantShowPaymentsPhaseThree: false,
        claimantUseFineosNewPaymentSchedule: true,
      });
    });
    const postDeployStartDate = "2022-05-17";
    const approvalDate = {
      "approved mid week after claim start date": dayjs(postDeployStartDate)
        .add(1, "day")
        .weekday(2)
        .format("YYYY-MM-DD"),
      "approved before claim start date": dayjs(postDeployStartDate)
        .add(-7, "day")
        .format("YYYY-MM-DD"),
      "approved on claim start date":
        dayjs(postDeployStartDate).format("YYYY-MM-DD"),
    };
    const approvalDateScenarios = Object.keys(approvalDate) as Array<
      keyof typeof approvalDate
    >;

    it.each(approvalDateScenarios)(
      "returns monday checkback date %s ",
      (state) => {
        renderPage(
          Payments,
          {
            addCustomSetup: setupHelper({
              absence_periods: [
                defaultAbsencePeriod,
                createAbsencePeriod({
                  period_type: "Reduced Schedule",
                  absence_period_start_date: dayjs(postDeployStartDate)
                    .add(2, "weeks")
                    .format("YYYY-MM-DD"),
                  absence_period_end_date: dayjs(postDeployStartDate)
                    .add(2, "weeks")
                    .add(4, "months")
                    .format("YYYY-MM-DD"),
                  reason: "Child Bonding",
                }),
              ],
              approvalDate: approvalDate[state],
              includeApprovalNotice: true,
            }),
          },
          props
        );

        const date = screen.getByText("will be scheduled on", { exact: false });
        const dayOfWeekCheckbackDate = dayjs(
          date.textContent?.match(/(?<=on )[^.]+/)?.[0]
        );
        expect(dayOfWeekCheckbackDate.day()).toBe(1);
        expect(screen.getByTestId("your-payments-intro")).toMatchSnapshot();
      }
    );
  });
});
