import Document, { DocumentType } from "../../../src/models/Document";
import Status, { LeaveDetails } from "../../../src/pages/applications/status";
import { cleanup, render, screen } from "@testing-library/react";
import AppErrorInfo from "../../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../../src/models/AppErrorInfoCollection";
import ClaimDetail from "../../../src/models/ClaimDetail";
import DocumentCollection from "../../../src/models/DocumentCollection";
import LeaveReason from "../../../src/models/LeaveReason";
import { ManagedRequirement } from "../../../src/models/Claim";
import React from "react";
import { ReasonQualifier } from "../../../src/models/BenefitsApplication";
import { mockRouter } from "next/router";
import { renderPage } from "../../test-utils";
import routes from "../../../src/routes";

jest.mock("next/router");

mockRouter.asPath = routes.applications.status;

const DOCUMENTS = [
  new Document({
    application_id: "mock-application-id",
    content_type: "image/png",
    created_at: "2020-04-05",
    document_type: DocumentType.denialNotice,
    fineos_document_id: "fineos-id-4",
    name: "legal notice 1",
  }),
  new Document({
    application_id: "not-my-application-id",
    content_type: "image/png",
    created_at: "2020-04-05",
    document_type: DocumentType.requestForInfoNotice,
    fineos_document_id: "fineos-id-5",
    name: "legal notice 2",
  }),
  new Document({
    application_id: "mock-application-id",
    content_type: "image/png",
    created_at: "2020-04-05",
    document_type: DocumentType.identityVerification,
    fineos_document_id: "fineos-id-6",
    name: "non-legal notice 1",
  }),
  new Document({
    application_id: "mock-application-id",
    content_type: "image/png",
    created_at: "2020-04-05",
    document_type: DocumentType.requestForInfoNotice,
    fineos_document_id: "fineos-id-7",
    name: "legal notice 3",
  }),
];

const renderWithClaimDocuments = (appLogicHook, documents = []) => {
  appLogicHook.documents.loadAll = jest.fn();
  appLogicHook.documents.documents = new DocumentCollection(documents);
  appLogicHook.documents.hasLoadedClaimDocuments = () => !!documents.length;
  appLogicHook.documents.download = jest.fn();
};

const setupHelper =
  (claimDetailAttrs, documents = []) =>
  (appLogicHook) => {
    appLogicHook.claims.claimDetail = claimDetailAttrs
      ? new ClaimDetail(claimDetailAttrs)
      : null;
    appLogicHook.claims.loadClaimDetail = jest.fn();
    renderWithClaimDocuments(appLogicHook, documents);
  };

const defaultClaimDetail = {
  application_id: "mock-application-id",
  fineos_absence_id: "mock-absence-case-id",
  employer: { employer_fein: "12-1234567" },
};
const props = {
  query: { absence_case_id: defaultClaimDetail.fineos_absence_id },
};

describe("Status", () => {
  beforeEach(() => {
    process.env.featureFlags = {
      claimantShowStatusPage: true,
    };
  });

  it("redirects page if feature flag is not enabled", () => {
    process.env.featureFlags = {
      claimantShowStatusPage: false,
    };

    const goToSpy = jest.fn();
    renderPage(
      Status,
      {
        addCustomSetup: (appLogicHook) => {
          appLogicHook.claims.loadClaimDetail = jest.fn();
          appLogicHook.portalFlow.goTo = goToSpy;
        },
      },
      props
    );

    expect(goToSpy).toHaveBeenCalledWith(routes.applications.index);
  });

  it("renders the page with back button if error exists", () => {
    renderPage(
      Status,
      {
        addCustomSetup: (appLogicHook) => {
          appLogicHook.claims.loadClaimDetail = jest.fn();
          appLogicHook.appErrors = new AppErrorInfoCollection([
            new AppErrorInfo(),
          ]);
        },
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
    const loadClaimDetailSpy = jest.fn();
    renderPage(
      Status,
      {
        addCustomSetup: (appLogicHook) => {
          appLogicHook.claims.loadClaimDetail = loadClaimDetailSpy;
        },
      },
      props
    );

    expect(loadClaimDetailSpy).toHaveBeenCalledWith("mock-absence-case-id");
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
            absence_case_id: defaultClaimDetail.fineos_absence_id,
          },
        }
      );
      expect(screen.getByRole("region")).toBeInTheDocument();
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
            absence_case_id: defaultClaimDetail.fineos_absence_id,
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
            absence_case_id: defaultClaimDetail.fineos_absence_id,
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

    it("displays if claimant has pregnancy but not bonding claims", () => {
      renderPage(
        Status,
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

    it("does not display if claimant has bonding AND pregnancy claims", () => {
      renderPage(
        Status,
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

    it("does not display if claimant has Denied claims", () => {
      renderPage(
        Status,
        {
          addCustomSetup: setupHelper({
            ...defaultClaimDetail,
            absence_periods: [
              {
                period_type: "Reduced",
                reason: LeaveReason.pregnancy,
                request_decision: "Denied",
              },
            ],
          }),
        },
        props
      );

      expect(screen.queryByRole("region")).not.toBeInTheDocument();
    });

    it("does not display if claimant has Withdrawn claims", () => {
      renderPage(
        Status,
        {
          addCustomSetup: setupHelper({
            ...defaultClaimDetail,
            absence_periods: [
              {
                period_type: "Reduced",
                reason: LeaveReason.bonding,
                reason_qualifier_one: "Newborn",
                request_decision: "Withdrawn",
              },
            ],
          }),
        },
        props
      );

      expect(screen.queryByRole("region")).not.toBeInTheDocument();
    });
  });

  describe("ViewYourNotices", () => {
    it("shows a spinner while loading", () => {
      renderPage(
        Status,
        {
          addCustomSetup: setupHelper({ ...defaultClaimDetail }),
        },
        props
      );

      expect(screen.getByRole("progressbar")).toBeInTheDocument();
    });

    it("displays only legal notices for the current application_id", () => {
      renderPage(
        Status,
        {
          addCustomSetup: setupHelper({ ...defaultClaimDetail }, DOCUMENTS),
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
      renderPage(
        Status,
        {
          addCustomSetup: setupHelper({ ...defaultClaimDetail }, [
            DOCUMENTS[1],
          ]),
        },
        props
      );

      expect(
        screen.getByText(
          /Once we’ve made a decision, you can download the decision notice here. You’ll also get an email notification./
        )
      ).toBeInTheDocument();
    });
  });

  it("includes a button to upload additional documents", () => {
    renderPage(
      Status,
      {
        addCustomSetup: setupHelper({ ...defaultClaimDetail }, [DOCUMENTS[1]]),
      },
      props
    );

    expect(screen.getByRole("link", { name: "Upload additional documents" }))
      .toMatchInlineSnapshot(`
      <a
        class="usa-button measure-6 margin-bottom-3"
        href="/applications/upload?absence_case_id=mock-absence-case-id"
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
        {
          period_type: "Reduced",
          absence_period_start_date: "2021-06-01",
          absence_period_end_date: "2021-06-08",
          request_decision: "Approved",
          fineos_leave_request_id: "PL-14432-0000002026",
          reason: LeaveReason.bonding,
          reason_qualifier_one: "Newborn",
        },
        {
          period_type: "Reduced Leave",
          absence_period_start_date: "2021-08-01",
          absence_period_end_date: "2021-08-08",
          request_decision: "Pending",
          fineos_leave_request_id: "PL-14434-0000002026",
          reason: LeaveReason.pregnancy,
          reason_qualifier_one: "Postnatal Disability",
        },
        {
          period_type: "Continuous",
          absence_period_start_date: "2021-08-01",
          absence_period_end_date: "2021-08-08",
          request_decision: "Withdrawn",
          fineos_leave_request_id: "PL-14434-0000002326",
          reason: LeaveReason.medical,
        },
      ],
    });

    it("does not render LeaveDetails if absenceDetails not given", () => {
      const { container } = render(<LeaveDetails />);
      expect(container).toBeEmptyDOMElement();
    });

    it("renders page separated by keys if object of absenceDetails has more keys", () => {
      const { container } = render(
        <LeaveDetails absenceDetails={CLAIM_DETAIL.absencePeriodsByReason} />
      );

      expect(container).toMatchSnapshot();
    });

    it("renders page with one section if absenceDetails has only one key", () => {
      const { container } = render(
        <LeaveDetails
          absenceDetails={{
            [LeaveReason.medical]:
              CLAIM_DETAIL.absencePeriodsByReason[LeaveReason.medical],
          }}
        />
      );

      expect(container).toMatchSnapshot();
    });
  });

  describe("timeline", () => {
    it("is not displayed if there are no pending absence periods", () => {
      const absence_periods = [
        "Withdrawn",
        "Cancelled",
        "Approved",
        "Denied",
      ].map((request_decision, fineos_leave_request_id) => ({
        fineos_leave_request_id,
        request_decision,
        period_type: "Continuous",
        reason: LeaveReason.medical,
      }));

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
      const absence_periods = [
        "Withdrawn",
        "Cancelled",
        "Approved",
        "Pending",
        "Denied",
      ].map((request_decision, fineos_leave_request_id) => ({
        fineos_leave_request_id,
        request_decision,
        period_type: "Continuous",
        reason: LeaveReason.medical,
      }));

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

      const claimDetailAttrs = {
        ...defaultClaimDetail,
        absence_periods: [
          {
            period_type: "Continuous",
            request_decision: "Pending",
            reason: randomReason,
          },
        ],
      };

      it("shows timeline with generic follow up dates when there are no open managed requirements with follow up dates", () => {
        renderPage(
          Status,
          {
            addCustomSetup: setupHelper({
              ...claimDetailAttrs,
              managed_requirements: [
                new ManagedRequirement({
                  follow_up_date: null,
                  status: "Open",
                }),
                new ManagedRequirement({
                  follow_up_date: "2022-01-01",
                  status: "Completed",
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
                new ManagedRequirement({
                  follow_up_date: "2021-01-01",
                  status: "Completed",
                }),
                new ManagedRequirement({
                  follow_up_date: "2021-01-01",
                  status: "Suppressed",
                }),
                new ManagedRequirement({
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
      const claimDetailAttrs = {
        ...defaultClaimDetail,
        absence_periods: [
          {
            period_type: "Continuous",
            request_decision: "Pending",
            reason: LeaveReason.bonding,
            reason_qualifier_one: ReasonQualifier.newBorn,
          },
        ],
      };

      const documents = [
        new Document({
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
                  new ManagedRequirement({
                    follow_up_date: null,
                    status: "Open",
                  }),
                  new ManagedRequirement({
                    follow_up_date: "2022-01-01",
                    status: "Completed",
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
                  new ManagedRequirement({
                    follow_up_date: "2021-01-01",
                    status: "Completed",
                  }),
                  new ManagedRequirement({
                    follow_up_date: "2021-01-01",
                    status: "Suppressed",
                  }),
                  new ManagedRequirement({
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
                {
                  period_type: "Continuous",
                  request_decision: "Pending",
                  reason: LeaveReason.bonding,
                  reason_qualifier_one: ReasonQualifier.newBorn,
                },
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
                {
                  period_type: "Continuous",
                  request_decision: "Pending",
                  reason: LeaveReason.bonding,
                  reason_qualifier_one: ReasonQualifier.newBorn,
                },
              ],
            }),
          },
          props
        );

        expect(screen.getByRole("link", { name: /Upload proof of birth/ }))
          .toMatchInlineSnapshot(`
          <a
            class="usa-button measure-12"
            href="/applications/upload/proof-of-birth?claim_id=mock-application-id&absence_case_id=mock-absence-case-id"
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
                {
                  period_type: "Continuous",
                  request_decision: "Pending",
                  reason: LeaveReason.bonding,
                  reason_qualifier_one: ReasonQualifier.fosterCare,
                },
              ],
            }),
          },
          props
        );

        expect(screen.getByRole("link", { name: /Upload proof of placement/ }))
          .toMatchInlineSnapshot(`
          <a
            class="usa-button measure-12"
            href="/applications/upload/proof-of-placement?claim_id=mock-application-id&absence_case_id=mock-absence-case-id"
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
                {
                  period_type: "Continuous",
                  request_decision: "Pending",
                  reason: LeaveReason.bonding,
                  reason_qualifier_one: ReasonQualifier.adoption,
                },
              ],
            }),
          },
          props
        );

        expect(screen.getByRole("link", { name: /Upload proof of adoption/ }))
          .toMatchInlineSnapshot(`
          <a
            class="usa-button measure-12"
            href="/applications/upload/proof-of-placement?claim_id=mock-application-id&absence_case_id=mock-absence-case-id"
          >
            Upload proof of adoption
          </a>
        `);
      });
    });
  });
});
