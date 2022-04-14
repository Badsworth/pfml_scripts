import {
  AbsencePeriod,
  AbsencePeriodRequestDecision,
} from "../../../../src/models/AbsencePeriod";
import {
  BenefitsApplicationDocument,
  DocumentType,
} from "../../../../src/models/Document";
import {
  DocumentsLoadError,
  RequestTimeoutError,
} from "../../../../src/errors";
import Status, {
  LeaveDetails,
} from "../../../../src/pages/applications/status/index";
import { cleanup, render, screen } from "@testing-library/react";
import { createAbsencePeriod, renderPage } from "../../../test-utils";
import ApiResourceCollection from "src/models/ApiResourceCollection";
import { AppLogic } from "../../../../src/hooks/useAppLogic";
import ClaimDetail from "../../../../src/models/ClaimDetail";
import { Holiday } from "../../../../src/models/Holiday";
import LeaveReason from "../../../../src/models/LeaveReason";
import { Payment } from "../../../../src/models/Payment";
import React from "react";
import { ReasonQualifier } from "../../../../src/models/BenefitsApplication";
import { createMockBenefitsApplicationDocument } from "../../../../lib/mock-helpers/createMockDocument";
import { createMockManagedRequirement } from "../../../../lib/mock-helpers/createMockManagedRequirement";
import { createMockPayment } from "lib/mock-helpers/createMockPayment";
// @ts-expect-error This should eventually be removed, in favor of setting the pathname option in renderPage
import { mockRouter } from "next/router";
import routes from "../../../../src/routes";

jest.mock("next/router");

mockRouter.asPath = routes.applications.status.claim;

const DOCUMENTS: BenefitsApplicationDocument[] = [
  createMockBenefitsApplicationDocument({
    application_id: "mock-application-id",
    content_type: "image/png",
    created_at: "2020-04-05",
    document_type: DocumentType.denialNotice,
    fineos_document_id: "fineos-id-4",
    name: "legal notice 1",
  }),
  createMockBenefitsApplicationDocument({
    application_id: "not-my-application-id",
    content_type: "image/png",
    created_at: "2020-04-05",
    document_type: DocumentType.requestForInfoNotice,
    fineos_document_id: "fineos-id-5",
    name: "legal notice 2",
  }),
  createMockBenefitsApplicationDocument({
    application_id: "mock-application-id",
    content_type: "image/png",
    created_at: "2020-04-05",
    document_type: DocumentType.identityVerification,
    fineos_document_id: "fineos-id-6",
    name: "non-legal notice 1",
  }),
  createMockBenefitsApplicationDocument({
    application_id: "mock-application-id",
    content_type: "image/png",
    created_at: "2020-04-05",
    document_type: DocumentType.requestForInfoNotice,
    fineos_document_id: "fineos-id-7",
    name: "legal notice 3",
  }),
];

const approvalNotice = createMockBenefitsApplicationDocument({
  application_id: "mock-application-id",
  content_type: "image/png",
  created_at: "2020-04-05",
  document_type: DocumentType.approvalNotice,
  fineos_document_id: "fineos-id-8",
  name: "legal notice 3",
});

const createDocuments = (
  documents: BenefitsApplicationDocument[] = [],
  includeApprovalNotice: boolean
) => {
  return new ApiResourceCollection<BenefitsApplicationDocument>(
    "fineos_document_id",
    includeApprovalNotice ? [...documents, approvalNotice] : documents
  );
};

const setupHelper =
  (
    claimDetailAttrs?: Partial<ClaimDetail>,
    documents: BenefitsApplicationDocument[] = [],
    errors: Error[] = [],
    loadClaimDetailMock: jest.Mock = jest.fn(),
    payments: Partial<Payment> = defaultPayments,
    includeApprovalNotice = true,
    hasLoadedClaimDocumentsValue = true,
    holidays: Holiday[] = defaultHolidays
  ) =>
  (appLogicHook: AppLogic) => {
    appLogicHook.claims.claimDetail = claimDetailAttrs
      ? new ClaimDetail(claimDetailAttrs)
      : undefined;
    appLogicHook.claims.loadClaimDetail = loadClaimDetailMock;
    appLogicHook.errors = errors;
    appLogicHook.holidays.holidays = holidays;
    appLogicHook.holidays.loadHolidays = jest.fn();
    appLogicHook.holidays.hasLoadedHolidays = true;
    appLogicHook.holidays.isLoadingHolidays = false;
    appLogicHook.payments.loadPayments = jest.fn();
    appLogicHook.payments.loadedPaymentsData = new Payment(payments);
    appLogicHook.payments.hasLoadedPayments = () => true;

    appLogicHook.documents.loadAll = jest.fn();
    appLogicHook.documents.download = jest.fn();
    appLogicHook.documents.documents = createDocuments(
      documents,
      includeApprovalNotice
    );
    appLogicHook.documents.hasLoadedClaimDocuments = () =>
      hasLoadedClaimDocumentsValue;
  };

const defaultClaimDetail: Partial<ClaimDetail> = {
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
};

const defaultPayments = {
  absence_case_id: "NTN-12345-ABS-01",
  payments: [
    createMockPayment({ status: "Sent to bank" }, true),
    createMockPayment({ status: "Delayed", sent_to_bank_date: null }, true),
    createMockPayment({ status: "Pending", sent_to_bank_date: null }, true),
    createMockPayment({ status: "Sent to bank" }, true),
  ],
};

const defaultHolidays = [{ name: "Memorial Day", date: "2022-05-30" }];
const defaultHolidayAlertText =
  "Due to the upcoming holiday, payments may be delayed by one business day.";
const props = {
  query: { absence_id: defaultClaimDetail.fineos_absence_id },
};

describe("Status", () => {
  describe("Payments tab display", () => {
    it("does not show StatusNavigationTabs if feature flag is enabled, claim has no payments, and is not approved", () => {
      renderPage(
        Status,
        {
          addCustomSetup: setupHelper(
            {
              ...defaultClaimDetail,
              absence_periods: [
                createAbsencePeriod({
                  period_type: "Reduced Schedule",
                  reason: LeaveReason.bonding,
                  request_decision: "Pending",
                  reason_qualifier_one: "Newborn",
                }),
              ],
            },
            [], // documents, default
            [], // errors, default
            jest.fn(), // loadClaimDetailMock, default
            new Payment(), // payments, default
            false // don't include the approval notice
          ),
        },
        props
      );

      expect(
        screen.queryByRole("link", { name: "Payments" })
      ).not.toBeInTheDocument();
    });

    it("shows payment tab if there are payments and claim is approved", () => {
      renderPage(
        Status,
        {
          addCustomSetup: setupHelper(
            defaultClaimDetail,
            [], // documents, default
            [], // errors, default
            jest.fn(), // loadClaimDetailMock, default
            defaultPayments // payments, default, but set explicitly to make this clearer
          ),
        },
        props
      );
      expect(
        screen.queryByRole("link", { name: "Payments" })
      ).toBeInTheDocument();
    });

    it("shows payment tab if there are no payments and claim is approved", () => {
      renderPage(
        Status,
        {
          addCustomSetup: setupHelper(
            defaultClaimDetail,
            [], // documents, default
            [], // errors, default
            jest.fn(), // loadClaimDetailMock, default
            new Payment() // payments, none
          ),
        },
        props
      );

      expect(
        screen.queryByRole("link", { name: "Payments" })
      ).toBeInTheDocument();
    });

    it("shows payment tab if there are payments and claim is not approved", () => {
      renderPage(
        Status,
        {
          addCustomSetup: setupHelper(
            {
              ...defaultClaimDetail,
              absence_periods: [
                createAbsencePeriod({
                  period_type: "Reduced Schedule",
                  reason: LeaveReason.bonding,
                  request_decision: "Pending",
                  reason_qualifier_one: "Newborn",
                }),
              ],
            },
            [], // documents, default
            [], // errors, default
            jest.fn(), // loadClaimDetailMock, default
            defaultPayments, // payments, default, but need some for this test
            false // don't include the approval notice
          ),
        },
        props
      );

      expect(
        screen.queryByRole("link", { name: "Payments" })
      ).toBeInTheDocument();
    });
  });

  it("redirects to 404 if there's no absence case ID", () => {
    renderPage(
      Status,
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

  it("renders the page if the only errors are DocumentsLoadError", () => {
    const errors = [new DocumentsLoadError("mock_application_id")];

    const { container } = renderPage(
      Status,
      {
        addCustomSetup: setupHelper({ ...defaultClaimDetail }, [], errors),
      },
      props
    );

    expect(container).toMatchSnapshot();
  });

  it("renders the page with only a back button if non-DocumentsLoadErrors exists", () => {
    const errors = [new RequestTimeoutError("mock_application_id")];
    renderPage(
      Status,
      {
        addCustomSetup: setupHelper({ ...defaultClaimDetail }, [], errors),
      },
      props
    );

    expect(
      screen.getByRole("link", { name: "Back to your applications" })
    ).toBeInTheDocument();
  });

  it("shows a spinner if there is no claim detail", () => {
    renderPage(
      Status,
      {
        addCustomSetup: setupHelper(),
      },
      props
    );

    expect(screen.getByRole("progressbar")).toBeInTheDocument();
  });

  it("fetches claim detail on if none is loaded", () => {
    const loadClaimDetailMock = jest.fn();
    renderPage(
      Status,
      {
        addCustomSetup: setupHelper(
          { ...defaultClaimDetail },
          [],
          [], // errors, default
          loadClaimDetailMock
        ),
      },
      props
    );

    expect(loadClaimDetailMock).toHaveBeenCalledWith("mock-absence-case-id");
  });

  it("renders the page with claim detail", () => {
    const { container } = renderPage(
      Status,
      {
        addCustomSetup: setupHelper({ ...defaultClaimDetail }),
      },
      props
    );

    expect(container).toMatchSnapshot();
  });

  it("renders the page with claim detail when there is absence_case_id in query", () => {
    const { container } = renderPage(
      Status,
      {
        addCustomSetup: setupHelper({ ...defaultClaimDetail }),
      },
      { query: { absence_case_id: defaultClaimDetail.fineos_absence_id } }
    );

    expect(container).toMatchSnapshot();
  });

  describe("success alert", () => {
    it("renders success alert when document type param is given", () => {
      renderPage(
        Status,
        {
          addCustomSetup: setupHelper({
            ...defaultClaimDetail,
          }),
        },
        {
          query: {
            uploaded_document_type: "proof-of-birth",
            claim_id: "12342323",
            absence_id: defaultClaimDetail.fineos_absence_id,
          },
        }
      );

      expect(
        screen.getByRole("heading", {
          name: "You've successfully submitted your proof of birth documents",
        })
      ).toBeInTheDocument();
    });

    it("displays the category message depending on uploaded document type", () => {
      renderPage(
        Status,
        {
          addCustomSetup: setupHelper({
            ...defaultClaimDetail,
          }),
        },
        {
          query: {
            uploaded_document_type: "state-id",
            claim_id: "12342323",
            absence_id: defaultClaimDetail.fineos_absence_id,
          },
        }
      );

      expect(
        screen.getByRole("heading", {
          name: "You've successfully submitted your identification documents",
        })
      ).toBeInTheDocument();
      cleanup();
      renderPage(
        Status,
        {
          addCustomSetup: setupHelper({
            ...defaultClaimDetail,
          }),
        },
        {
          query: {
            uploaded_document_type: "family-member-medical-certification",
            claim_id: "12342323",
            absence_id: defaultClaimDetail.fineos_absence_id,
          },
        }
      );

      expect(
        screen.getByRole("heading", {
          name: "You've successfully submitted your certification form",
        })
      ).toBeInTheDocument();
    });
  });

  describe("info alert", () => {
    it("displays if claimant has bonding-newborn but not pregnancy claims", () => {
      renderPage(
        Status,
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

      const bondingAlertText =
        "If you are giving birth, you may also be eligible for paid medical leave";
      expect(
        screen.getByText(bondingAlertText, { exact: false })
      ).toBeInTheDocument();
    });

    it("displays if claimant has pregnancy but not bonding claims", () => {
      renderPage(
        Status,
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

      const pregnancyAlertText =
        "You may be able to take up to 12 weeks of paid family leave to bond with your child after your medical leave ends.";
      expect(
        screen.getByText(pregnancyAlertText, { exact: false })
      ).toBeInTheDocument();
    });

    it("displays if claimant has In Review claim status", () => {
      renderPage(
        Status,
        {
          addCustomSetup: setupHelper({
            ...defaultClaimDetail,
            absence_periods: [
              createAbsencePeriod({
                period_type: "Reduced Schedule",
                reason: LeaveReason.pregnancy,
                request_decision: "In Review",
              }),
            ],
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

    it("displays if claimant has Projected claim status", () => {
      renderPage(
        Status,
        {
          addCustomSetup: setupHelper({
            ...defaultClaimDetail,
            absence_periods: [
              createAbsencePeriod({
                period_type: "Reduced Schedule",
                reason: LeaveReason.pregnancy,
                request_decision: "Projected",
              }),
            ],
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

    it("does not display if claimant has bonding AND pregnancy claims", () => {
      renderPage(
        Status,
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

    it("does not display if claimant has Denied claims", () => {
      renderPage(
        Status,
        {
          addCustomSetup: setupHelper(
            {
              ...defaultClaimDetail,
              absence_periods: [
                createAbsencePeriod({
                  period_type: "Reduced Schedule",
                  reason: LeaveReason.pregnancy,
                  request_decision: "Denied",
                }),
              ],
            },
            [], // documents, default
            [], // errors, default
            jest.fn(), // loadClaimDetailMock, default
            new Payment(), // payments, none
            false // don't include the approval notice
          ),
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

    it("does not display if claimant has Withdrawn claims", () => {
      renderPage(
        Status,
        {
          addCustomSetup: setupHelper(
            {
              ...defaultClaimDetail,
              absence_periods: [
                createAbsencePeriod({
                  period_type: "Reduced Schedule",
                  reason: LeaveReason.bonding,
                  reason_qualifier_one: "Newborn",
                  request_decision: "Withdrawn",
                }),
              ],
            },
            [], // documents, default
            [], // errors, default
            jest.fn(), // loadClaimDetailMock, default
            new Payment(), // payments, none
            false // don't include the approval notice
          ),
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
  });

  describe("holiday alert", () => {
    it("doesn't show the holiday alert when there are holidays, but the claimantShowPaymentsPhaseThree feature flag is off", () => {
      process.env.featureFlags = JSON.stringify({
        showHolidayAlert: true,
        claimantShowPaymentsPhaseThree: false,
      });

      renderPage(
        Status,
        {
          addCustomSetup: setupHelper(
            { ...defaultClaimDetail },
            [], // documents, default
            [], // errors, default
            jest.fn(), // loadClaimDetailMock, default
            defaultPayments, // payments, default
            true, // approval notice, default
            true, // loaded documents, default
            defaultHolidays // holidays, default
          ),
        },
        props
      );
      expect(
        screen.queryByText(defaultHolidayAlertText)
      ).not.toBeInTheDocument();
    });

    it("doesn't show the holiday alert when there are holidays, but the showHolidayAlert feature flag is off", () => {
      process.env.featureFlags = JSON.stringify({
        showHolidayAlert: false,
        claimantShowPaymentsPhaseThree: true,
      });

      renderPage(
        Status,
        {
          addCustomSetup: setupHelper(
            { ...defaultClaimDetail },
            [], // documents, default
            [], // errors, default
            jest.fn(), // loadClaimDetailMock, default
            defaultPayments, // payments, default
            true, // approval notice, default
            true, // loaded documents, default
            defaultHolidays // holidays, default
          ),
        },
        props
      );
      expect(
        screen.queryByText(defaultHolidayAlertText)
      ).not.toBeInTheDocument();
    });

    it("doesn't show the holiday alert when there are no holidays", () => {
      process.env.featureFlags = JSON.stringify({
        showHolidayAlert: true,
        claimantShowPaymentsPhaseThree: true,
      });

      renderPage(
        Status,
        {
          addCustomSetup: setupHelper(
            { ...defaultClaimDetail },
            [], // documents, default
            [], // errors, default
            jest.fn(), // loadClaimDetailMock, default
            defaultPayments, // payments, default
            true, // approval notice, default
            true, // loaded documents, default
            [] // no holidays
          ),
        },
        props
      );
      expect(
        screen.queryByText(defaultHolidayAlertText)
      ).not.toBeInTheDocument();
    });

    it("shows the holiday alert when there are holidays", () => {
      process.env.featureFlags = JSON.stringify({
        showHolidayAlert: true,
        claimantShowPaymentsPhaseThree: true,
      });

      renderPage(
        Status,
        {
          addCustomSetup: setupHelper(
            { ...defaultClaimDetail },
            [], // documents, default
            [], // errors, default
            jest.fn(), // loadClaimDetailMock, default
            defaultPayments, // payments, default
            true, // approval notice, default
            true, // loaded documents, default
            defaultHolidays // holidays, default
          ),
        },
        props
      );
      expect(screen.queryByText(defaultHolidayAlertText)).toBeInTheDocument();
    });
  });

  describe("ViewYourNotices", () => {
    it("shows a spinner while loading", () => {
      renderPage(
        Status,
        {
          addCustomSetup: setupHelper(
            { ...defaultClaimDetail },
            [], // documents, default
            [], // errors, default
            jest.fn(), // loadClaimDetailMock, default
            new Payment(), // payments, none
            false, // don't include approval notice
            false // doesn't have loaded documents
          ),
        },
        props
      );

      expect(screen.getByRole("progressbar")).toBeInTheDocument();
    });

    it("displays only legal notices for the current application_id", () => {
      renderPage(
        Status,
        {
          addCustomSetup: setupHelper(
            { ...defaultClaimDetail },
            DOCUMENTS // include documents
          ),
        },
        props
      );
      expect(
        screen.getByRole("button", { name: "Denial notice (PDF)" })
      ).toBeInTheDocument();
      expect(
        screen.getByRole("button", {
          name: "Request for more information (PDF)",
        })
      ).toBeInTheDocument();
    });

    it("displays the fallback text if there are no legal notices", () => {
      const nonLegalNotice = createMockBenefitsApplicationDocument({
        application_id: "mock-application-id",
        content_type: "image/png",
        created_at: "2020-04-05",
        document_type: DocumentType.identityVerification,
        fineos_document_id: "fineos-id-6",
        name: "non-legal notice 1",
      });

      renderPage(
        Status,
        {
          addCustomSetup: setupHelper(
            defaultClaimDetail,
            [nonLegalNotice], // documents
            [], // errors, default
            jest.fn(), // loadClaimDetailMock, default
            defaultPayments, // payments, default
            false // dont include the approval notice
          ),
        },
        props
      );

      expect(
        screen.getByText(
          /We will notify you once we’ve made a decision. You’ll be able to download the decision notice on this website./
        )
      ).toBeInTheDocument();
    });

    it("displays status timeline when the claim has 'Approved' status, but no approval notice document", () => {
      renderPage(
        Status,
        {
          addCustomSetup: setupHelper(
            defaultClaimDetail,
            [], // documents, default
            [], // errors, default
            jest.fn(), // loadClaimDetailMock, default
            defaultPayments, // payments, default
            false // dont include the approval notice
          ),
        },
        props
      );

      expect(
        screen.getByText(
          /Notices usually appear within 30 minutes after we update the status of your application./
        )
      ).toBeInTheDocument();
    });

    it("doesn't display status timeline when claim has 'Approved' status and approval notice document is present", () => {
      renderPage(
        Status,
        {
          addCustomSetup: setupHelper(
            defaultClaimDetail,
            [], // documents, default
            [], // errors, default
            jest.fn(), // loadClaimDetailMock, default
            defaultPayments, // payments, default
            true // default, include the approval notice
          ),
        },
        props
      );

      expect(
        screen.queryByText(
          /Notices usually appear within 30 minutes after we update the status of your application./
        )
      ).not.toBeInTheDocument();
    });
  });

  it("includes a button to upload additional documents if there is a pending absence period", () => {
    const request_decisions = [
      "Withdrawn",
      "Cancelled",
      "Approved",
      "Pending",
      "Denied",
    ] as const;
    const absence_periods = request_decisions.map(
      (request_decision, fineos_leave_request_id) =>
        createAbsencePeriod({
          fineos_leave_request_id: fineos_leave_request_id.toString(),
          request_decision,
          period_type: "Continuous",
          reason: LeaveReason.medical,
        })
    );

    renderPage(
      Status,
      {
        addCustomSetup: setupHelper({
          ...defaultClaimDetail,
          absence_periods,
        }),
      },
      props
    );

    expect(screen.getByRole("link", { name: "Upload additional documents" }))
      .toMatchInlineSnapshot(`
      <a
        class="usa-button margin-top-3"
        href="/applications/upload?absence_id=mock-absence-case-id"
      >
        Upload additional documents
      </a>
    `);
  });

  /** Test LeaveDetails component */
  describe("LeaveDetails", () => {
    const CLAIM_DETAIL = new ClaimDetail({
      fineos_absence_id: "fineos-abence-id",
      absence_periods: [
        createAbsencePeriod({
          period_type: "Reduced Schedule",
          absence_period_start_date: "2021-06-01",
          absence_period_end_date: "2021-06-08",
          request_decision: "Approved",
          fineos_leave_request_id: "PL-14432-0000002026",
          reason: LeaveReason.bonding,
          reason_qualifier_one: "Newborn",
        }),
        createAbsencePeriod({
          period_type: "Reduced Schedule",
          absence_period_start_date: "2021-08-01",
          absence_period_end_date: "2021-08-08",
          request_decision: "Pending",
          fineos_leave_request_id: "PL-14434-0000002026",
          reason: LeaveReason.pregnancy,
          reason_qualifier_one: "Postnatal Disability",
        }),
        createAbsencePeriod({
          period_type: "Continuous",
          absence_period_start_date: "2021-08-01",
          absence_period_end_date: "2021-08-08",
          request_decision: "Withdrawn",
          fineos_leave_request_id: "PL-14434-0000002326",
          reason: LeaveReason.medical,
        }),
      ],
    });

    it("does not render LeaveDetails if absenceDetails not given", () => {
      const { container } = render(
        <LeaveDetails absenceId={CLAIM_DETAIL.fineos_absence_id} />
      );
      expect(container).toBeEmptyDOMElement();
    });

    it("renders page separated by keys if object of absenceDetails has more keys", () => {
      const { container } = render(
        <LeaveDetails
          absenceId={CLAIM_DETAIL.fineos_absence_id}
          absenceDetails={AbsencePeriod.groupByReason(
            CLAIM_DETAIL.absence_periods
          )}
        />
      );

      expect(container).toMatchSnapshot();
    });

    it("renders page with one section if absenceDetails has only one key", () => {
      const { container } = render(
        <LeaveDetails
          absenceId={CLAIM_DETAIL.fineos_absence_id}
          absenceDetails={{
            [LeaveReason.medical]: AbsencePeriod.groupByReason(
              CLAIM_DETAIL.absence_periods
            )[LeaveReason.medical],
          }}
        />
      );

      expect(container).toMatchSnapshot();
    });

    it("renders track your payments link if isPaymentsTab is true", () => {
      render(
        <LeaveDetails
          absenceId={CLAIM_DETAIL.fineos_absence_id}
          isPaymentsTab
          absenceDetails={{
            [LeaveReason.medical]: AbsencePeriod.groupByReason(
              CLAIM_DETAIL.absence_periods
            )[LeaveReason.bonding],
          }}
        />
      );

      expect(
        screen.getByRole("link", { name: /Track your payment/ })
      ).toBeInTheDocument();
    });
  });

  describe("timeline", () => {
    it("is not displayed if there are no pending absence periods", () => {
      const request_decisions = [
        "Withdrawn",
        "Cancelled",
        "Approved",
        "Denied",
      ] as const;
      const absence_periods = request_decisions.map(
        (request_decision, fineos_leave_request_id) =>
          createAbsencePeriod({
            fineos_leave_request_id: fineos_leave_request_id.toString(),
            request_decision,
            period_type: "Continuous",
            reason: LeaveReason.medical,
          })
      );

      renderPage(
        Status,
        {
          addCustomSetup: setupHelper({
            ...defaultClaimDetail,
            absence_periods,
          }),
        },
        props
      );

      expect(screen.queryByTestId("timeline")).not.toBeInTheDocument();
    });

    it("is displayed if there is a pending absence period", () => {
      const request_decisions = [
        "Withdrawn",
        "Cancelled",
        "Approved",
        "Pending",
        "Denied",
      ] as const;
      const absence_periods = request_decisions.map(
        (request_decision, fineos_leave_request_id) =>
          createAbsencePeriod({
            fineos_leave_request_id: fineos_leave_request_id.toString(),
            request_decision,
            period_type: "Continuous",
            reason: LeaveReason.medical,
          })
      );

      renderPage(
        Status,
        {
          addCustomSetup: setupHelper({
            ...defaultClaimDetail,
            absence_periods,
          }),
        },
        props
      );

      const timeline = screen.getByTestId("timeline");
      expect(timeline).toBeInTheDocument();
      expect(timeline).toMatchSnapshot();
    });

    describe("when there is a pending caring, medical, or pregnancy absence period", () => {
      const randomReason = [
        LeaveReason.care,
        LeaveReason.medical,
        LeaveReason.pregnancy,
      ][Math.floor(Math.random() * 3)];

      const claimDetailAttrs: Partial<ClaimDetail> = {
        ...defaultClaimDetail,
        absence_periods: [
          createAbsencePeriod({
            period_type: "Continuous",
            request_decision: "Pending",
            reason: randomReason,
          }),
        ],
      };

      it("shows timeline with generic follow up dates when there are no open managed requirements with follow up dates", () => {
        renderPage(
          Status,
          {
            addCustomSetup: setupHelper({
              ...claimDetailAttrs,
              managed_requirements: [
                createMockManagedRequirement({
                  follow_up_date: null,
                  status: "Open",
                }),
                createMockManagedRequirement({
                  follow_up_date: "2022-01-01",
                  status: "Complete",
                }),
              ],
            }),
          },
          props
        );

        expect(screen.getByText(/10 business days/).closest("p"))
          .toMatchInlineSnapshot(`
          <p>
            Your employer has 
            <strong>
              10 business days
            </strong>
             to respond to your application.
          </p>
        `);
      });

      it("shows timeline with specific follow up dates when there is an open managed requirements with a follow up date", () => {
        renderPage(
          Status,
          {
            addCustomSetup: setupHelper({
              ...claimDetailAttrs,
              managed_requirements: [
                createMockManagedRequirement({
                  follow_up_date: "2021-01-01",
                  status: "Complete",
                }),
                createMockManagedRequirement({
                  follow_up_date: "2021-01-01",
                  status: "Suppressed",
                }),
                createMockManagedRequirement({
                  follow_up_date: "2022-12-01",
                  status: "Open",
                }),
              ],
            }),
          },
          props
        );

        expect(screen.getByText(/12\/1\/2022/).closest("p"))
          .toMatchInlineSnapshot(`
          <p>
            Your employer has until 
            <strong>
              12/1/2022
            </strong>
             to respond to your application.
          </p>
        `);
      });
    });

    describe("when there is a pending bonding absence period and claimant has submitted certification documents", () => {
      const claimDetailAttrs: Partial<ClaimDetail> = {
        ...defaultClaimDetail,
        absence_periods: [
          createAbsencePeriod({
            period_type: "Continuous",
            request_decision: "Pending",
            reason: LeaveReason.bonding,
            reason_qualifier_one: ReasonQualifier.newBorn,
          }),
        ],
      };

      const documents: BenefitsApplicationDocument[] = [
        createMockBenefitsApplicationDocument({
          application_id: defaultClaimDetail.application_id,
          document_type: DocumentType.certification[LeaveReason.bonding],
        }),
      ];

      it("shows timeline with generic follow up dates when there are no open managed requirements with follow up dates", () => {
        renderPage(
          Status,
          {
            addCustomSetup: setupHelper(
              {
                ...claimDetailAttrs,
                managed_requirements: [
                  createMockManagedRequirement({
                    follow_up_date: null,
                    status: "Open",
                  }),
                  createMockManagedRequirement({
                    follow_up_date: "2022-01-01",
                    status: "Complete",
                  }),
                ],
              },
              documents
            ),
          },
          props
        );

        expect(screen.getByText(/10 business days/).closest("p"))
          .toMatchInlineSnapshot(`
          <p>
            Your employer has 
            <strong>
              10 business days
            </strong>
             to respond to your application.
          </p>
        `);
      });

      it("shows timeline with specific follow up dates when there is an open managed requirements with a follow up date", () => {
        renderPage(
          Status,
          {
            addCustomSetup: setupHelper(
              {
                ...claimDetailAttrs,
                managed_requirements: [
                  createMockManagedRequirement({
                    follow_up_date: "2021-01-01",
                    status: "Complete",
                  }),
                  createMockManagedRequirement({
                    follow_up_date: "2021-01-01",
                    status: "Suppressed",
                  }),
                  createMockManagedRequirement({
                    follow_up_date: "2022-12-01",
                    status: "Open",
                  }),
                ],
              },
              documents
            ),
          },
          props
        );

        expect(screen.getByText(/12\/1\/2022/).closest("p"))
          .toMatchInlineSnapshot(`
          <p>
            Your employer has until 
            <strong>
              12/1/2022
            </strong>
             to respond to your application.
          </p>
        `);
      });
    });

    describe("when there is a pending bonding absence period and claimant has not uploaded certification documents", () => {
      it("shows follow up steps", () => {
        renderPage(
          Status,
          {
            addCustomSetup: setupHelper({
              ...defaultClaimDetail,
              absence_periods: [
                createAbsencePeriod({
                  period_type: "Continuous",
                  request_decision: "Pending",
                  reason: LeaveReason.bonding,
                  reason_qualifier_one: ReasonQualifier.newBorn,
                }),
              ],
            }),
          },
          props
        );

        expect(screen.getByTestId("timeline")).toMatchSnapshot();
      });

      it("shows link to upload proof of birth when reason qualifier is newborn", () => {
        renderPage(
          Status,
          {
            addCustomSetup: setupHelper({
              ...defaultClaimDetail,
              absence_periods: [
                createAbsencePeriod({
                  period_type: "Continuous",
                  request_decision: "Pending",
                  reason: LeaveReason.bonding,
                  reason_qualifier_one: ReasonQualifier.newBorn,
                }),
              ],
            }),
          },
          props
        );

        expect(screen.getByRole("link", { name: /Upload proof of birth/ }))
          .toMatchInlineSnapshot(`
          <a
            class="usa-button"
            href="/applications/upload/proof-of-birth?claim_id=mock-application-id&absence_id=mock-absence-case-id"
          >
            Upload proof of birth
          </a>
        `);
      });

      it("shows link to upload proof of placement when reason qualifier is foster", () => {
        renderPage(
          Status,
          {
            addCustomSetup: setupHelper({
              ...defaultClaimDetail,
              absence_periods: [
                createAbsencePeriod({
                  period_type: "Continuous",
                  request_decision: "Pending",
                  reason: LeaveReason.bonding,
                  reason_qualifier_one: ReasonQualifier.fosterCare,
                }),
              ],
            }),
          },
          props
        );

        expect(screen.getByRole("link", { name: /Upload proof of placement/ }))
          .toMatchInlineSnapshot(`
          <a
            class="usa-button"
            href="/applications/upload/proof-of-placement?claim_id=mock-application-id&absence_id=mock-absence-case-id"
          >
            Upload proof of placement
          </a>
        `);
      });

      it("shows link to upload proof of adoption when reason qualifier is foster", () => {
        renderPage(
          Status,
          {
            addCustomSetup: setupHelper({
              ...defaultClaimDetail,
              absence_periods: [
                createAbsencePeriod({
                  period_type: "Continuous",
                  request_decision: "Pending",
                  reason: LeaveReason.bonding,
                  reason_qualifier_one: ReasonQualifier.adoption,
                }),
              ],
            }),
          },
          props
        );

        expect(screen.getByRole("link", { name: /Upload proof of adoption/ }))
          .toMatchInlineSnapshot(`
          <a
            class="usa-button"
            href="/applications/upload/proof-of-placement?claim_id=mock-application-id&absence_id=mock-absence-case-id"
          >
            Upload proof of adoption
          </a>
        `);
      });
    });
  });

  describe("manage your application", () => {
    it("is not displayed if all the claim statuses on an application are Withdrawn, Cancelled, or Denied", () => {
      const request_decisions = ["Withdrawn", "Cancelled", "Denied"] as const;
      const absence_periods = request_decisions.map(
        (request_decision, fineos_leave_request_id) =>
          createAbsencePeriod({
            fineos_leave_request_id: fineos_leave_request_id.toString(),
            request_decision,
            period_type: "Continuous",
            reason: LeaveReason.medical,
          })
      );

      renderPage(
        Status,
        {
          addCustomSetup: setupHelper(
            {
              ...defaultClaimDetail,
              absence_periods,
            },
            [], // documents, default
            [], // errors, default
            jest.fn(), // loadClaimDetailMock, default
            new Payment(), // payments, none
            false // don't include the approval notice
          ),
        },
        props
      );

      expect(screen.queryByTestId("manageApplication")).not.toBeInTheDocument();
    });

    it("displays manage approved application link if any of the claim statuses on an application are Approved", () => {
      const request_decisions = [
        "Withdrawn",
        "Cancelled",
        "Approved",
        "Pending",
        "Denied",
      ] as const;
      const absence_periods = request_decisions.map(
        (request_decision, fineos_leave_request_id) =>
          createAbsencePeriod({
            fineos_leave_request_id: fineos_leave_request_id.toString(),
            request_decision,
            period_type: "Continuous",
            reason: LeaveReason.medical,
          })
      );

      renderPage(
        Status,
        {
          addCustomSetup: setupHelper({
            ...defaultClaimDetail,
            absence_periods,
          }),
        },
        props
      );

      const manageApprovedApplicationLink = screen.getByTestId(
        "manageApprovedApplicationLink"
      );
      expect(manageApprovedApplicationLink).toBeInTheDocument();
      expect(manageApprovedApplicationLink).toMatchSnapshot();
    });

    it("is displayed if any of the claim statuses on an application are Pending and none are Approved", () => {
      const request_decisions = [
        "Withdrawn",
        "Cancelled",
        "Pending",
        "Denied",
      ] as const;
      const absence_periods = request_decisions.map(
        (request_decision, fineos_leave_request_id) =>
          createAbsencePeriod({
            fineos_leave_request_id: fineos_leave_request_id.toString(),
            request_decision,
            period_type: "Continuous",
            reason: LeaveReason.medical,
          })
      );

      renderPage(
        Status,
        {
          addCustomSetup: setupHelper({
            ...defaultClaimDetail,
            absence_periods,
          }),
        },
        props
      );

      const manageApplication = screen.getByTestId("manageApplication");
      expect(manageApplication).toBeInTheDocument();
      expect(manageApplication).toMatchSnapshot();
    });
  });

  it.each(Object.values(AbsencePeriodRequestDecision))(
    "displays a description for the %s request decision",
    (request_decision) => {
      renderPage(
        Status,
        {
          addCustomSetup: setupHelper({
            ...defaultClaimDetail,
            absence_periods: [
              createAbsencePeriod({
                request_decision,
              }),
            ],
          }),
        },
        props
      );
      expect(screen.getByTestId("leaveStatusMessage")).toMatchSnapshot();
    }
  );

  describe("request a change", () => {
    it("displays request a change section if any of the claim statuses on an application are Approved and feature flag is on", () => {
      process.env.featureFlags = JSON.stringify({
        claimantShowModifications: true,
      });

      const request_decisions = [
        "Withdrawn",
        "Cancelled",
        "Approved",
        "Denied",
      ] as const;

      const absence_periods = request_decisions.map(
        (request_decision, fineos_leave_request_id) =>
          createAbsencePeriod({
            fineos_leave_request_id: fineos_leave_request_id.toString(),
            request_decision,
            period_type: "Continuous",
            reason: LeaveReason.medical,
          })
      );

      renderPage(
        Status,
        {
          addCustomSetup: setupHelper({
            ...defaultClaimDetail,
            absence_periods,
          }),
        },
        props
      );

      const requestChange = screen.getByTestId("requestChange");
      expect(requestChange).toBeInTheDocument();
      expect(requestChange).toMatchSnapshot();
    });

    it("displays withdraw a change section if any of the claim statuses on an application are Pending, none are Approved and feature flag is on", () => {
      process.env.featureFlags = JSON.stringify({
        claimantShowModifications: true,
      });

      const request_decisions = [
        "Withdrawn",
        "Cancelled",
        "Pending",
        "Denied",
      ] as const;

      const absence_periods = request_decisions.map(
        (request_decision, fineos_leave_request_id) =>
          createAbsencePeriod({
            fineos_leave_request_id: fineos_leave_request_id.toString(),
            request_decision,
            period_type: "Continuous",
            reason: LeaveReason.medical,
          })
      );

      renderPage(
        Status,
        {
          addCustomSetup: setupHelper({
            ...defaultClaimDetail,
            absence_periods,
          }),
        },
        props
      );

      const withdrawChange = screen.getByTestId("withdrawChange");
      expect(withdrawChange).toBeInTheDocument();
      expect(withdrawChange).toMatchSnapshot();
    });

    it("displays change request history if feature flag is on", () => {
      process.env.featureFlags = JSON.stringify({
        claimantShowModifications: true,
      });

      const request_decisions = [
        "Withdrawn",
        "Cancelled",
        "Pending",
        "Denied",
      ] as const;

      const absence_periods = request_decisions.map(
        (request_decision, fineos_leave_request_id) =>
          createAbsencePeriod({
            fineos_leave_request_id: fineos_leave_request_id.toString(),
            request_decision,
            period_type: "Continuous",
            reason: LeaveReason.medical,
          })
      );

      renderPage(
        Status,
        {
          addCustomSetup: setupHelper({
            ...defaultClaimDetail,
            absence_periods,
          }),
        },
        props
      );

      const changeRequestHistory = screen.getByTestId("changeRequestHistory");
      expect(changeRequestHistory).toBeInTheDocument();
      expect(changeRequestHistory).toMatchSnapshot();
    });

    it("doesn't display request change request sections if feature flag is off", () => {
      process.env.featureFlags = JSON.stringify({
        claimantShowModifications: false,
      });

      const request_decisions = [
        "Withdrawn",
        "Cancelled",
        "Approved",
        "Denied",
      ] as const;

      const absence_periods = request_decisions.map(
        (request_decision, fineos_leave_request_id) =>
          createAbsencePeriod({
            fineos_leave_request_id: fineos_leave_request_id.toString(),
            request_decision,
            period_type: "Continuous",
            reason: LeaveReason.medical,
          })
      );

      renderPage(
        Status,
        {
          addCustomSetup: setupHelper({
            ...defaultClaimDetail,
            absence_periods,
          }),
        },
        props
      );

      expect(screen.queryByTestId("requestChange")).not.toBeInTheDocument();
      expect(screen.queryByTestId("withdrawChange")).not.toBeInTheDocument();
      expect(
        screen.queryByTestId("changeRequestHistory")
      ).not.toBeInTheDocument();
    });
  });
});
