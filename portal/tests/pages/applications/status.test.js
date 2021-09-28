/**
 * This RTL test currently only tests the timeline portion
 * of the status page.
 * The full status page will be tested with PORTAL-706
 */
import ClaimDetail, { AbsencePeriod } from "../../../src/models/ClaimDetail";
import Document, { DocumentType } from "../../../src/models/Document";
import DocumentCollection from "../../../src/models/DocumentCollection";
import LeaveReason from "../../../src/models/LeaveReason";
import { ManagedRequirement } from "../../../src/models/Claim";
import { ReasonQualifier } from "../../../src/models/BenefitsApplication";
import Status from "../../../src/pages/applications/status";
import { mockRouter } from "next/router";
import { renderPage } from "../../test-utils";
import routes from "../../../src/routes";
import { screen } from "@testing-library/react";

jest.mock("next/router");

mockRouter.asPath = routes.applications.status;

const renderWithClaimDocuments = (appLogicHook, documents = []) => {
  appLogicHook.documents.loadAll = jest.fn();
  appLogicHook.documents.documents = new DocumentCollection(documents);
  appLogicHook.documents.hasLoadedDocuments = !!documents.length;
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

describe(Status, () => {
  describe("timeline", () => {
    it("is not displayed if there are no pending absence periods", () => {
      const absence_periods = [
        "Withdrawn",
        "Cancelled",
        "Approved",
        "Denied",
      ].map(
        (request_decision, fineos_leave_request_id) =>
          new AbsencePeriod({
            fineos_leave_request_id,
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
      const absence_periods = [
        "Withdrawn",
        "Cancelled",
        "Approved",
        "Pending",
        "Denied",
      ].map(
        (request_decision, fineos_leave_request_id) =>
          new AbsencePeriod({
            fineos_leave_request_id,
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

      const claimDetailAttrs = {
        ...defaultClaimDetail,
        absence_periods: [
          new AbsencePeriod({
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
          new AbsencePeriod({
            period_type: "Continuous",
            request_decision: "Pending",
            reason: LeaveReason.bonding,
            reason_qualifier_one: ReasonQualifier.newBorn,
          }),
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
                new AbsencePeriod({
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
                new AbsencePeriod({
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
                new AbsencePeriod({
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
                new AbsencePeriod({
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
