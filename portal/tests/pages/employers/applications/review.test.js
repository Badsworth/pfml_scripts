import Document, { DocumentType } from "../../../../src/models/Document";
import { render, screen, within } from "@testing-library/react";
import DocumentCollection from "../../../../src/models/DocumentCollection";
import LeaveReason from "../../../../src/models/LeaveReason";
import { MockEmployerClaimBuilder } from "../../../../tests-old/test-utils";
import { Review } from "../../../../src/pages/employers/applications/review";
import User from "../../../../src/models/User";
import { renderPage } from "../../../test-utils";
import { cloneDeep, merge } from "lodash";
import useAppLogic from "../../../../src/hooks/useAppLogic";

const DOCUMENTS = new DocumentCollection([
  new Document({
    content_type: "image/png",
    created_at: "2020-04-05",
    document_type: DocumentType.certification.medicalCertification,
    fineos_document_id: "fineos-id-4",
    name: "Medical cert doc",
  }),
  new Document({
    content_type: "application/pdf",
    created_at: "2020-01-02",
    document_type: DocumentType.approvalNotice,
    fineos_document_id: "fineos-id-1",
    name: "Approval notice doc",
  }),
  new Document({
    content_type: "application/pdf",
    created_at: "2020-02-01",
    document_type: DocumentType.certification[LeaveReason.care],
    fineos_document_id: "fineos-id-10",
    name: "Caring cert doc",
  }),
]);

/**
 * Asserts that the ReviewRow displays the correct text content.
 * @param {HTMLElement} node - the ReviewRow HTML element
 * @param {string} label
 * @param {string} description
 */
function assertReviewRow(node, label, description) {
  expect(within(node).queryByText(label)).toBeInTheDocument();
  expect(within(node).queryByText(description)).toBeInTheDocument();
}

describe("Review", () => {
  const goTo = jest.fn();
  const baseClaimBuilder = new MockEmployerClaimBuilder()
    .completed()
    .reviewable();
  const claimWithV1Eform = baseClaimBuilder.eformsV1().create();
  const claimWithV2Eform = baseClaimBuilder.eformsV2().create();
  const query = { absence_id: "NTN-111-ABS-01" };

  // TODO only use this OR renderV2Page
  const ReviewWithAppLogic = (providedProps) => {
    // default appLogic prop required by components using withUser.
    const defaultAppLogic = useAppLogic();
    defaultAppLogic.auth.requireLogin = jest.fn();
    defaultAppLogic.users.requireUserConsentToDataAgreement = jest.fn();
    defaultAppLogic.users.requireUserRole = jest.fn();
    defaultAppLogic.users.user = new User({
      consented_to_data_sharing: true,
      email_address: "unique_@miau.com",
    });

    // default props for the purposes of this test.
    const claim = providedProps.claim ?? claimWithV2Eform;
    defaultAppLogic.employers.claim = claim;
    defaultAppLogic.portalFlow.goTo = goTo;

    const defaultProps = {
      appLogic: defaultAppLogic,
      claim,
      query,
    };

    const props = merge({}, defaultProps, providedProps);
    return <Review {...props} />;
  };

  function renderV2Page(providedOptions = {}, providedProps = {}) {
    const claim = providedProps.claim ?? claimWithV2Eform;

    const defaultOptions = {
      addCustomSetup: (appLogic) => {
        appLogic.employers.claim = claim;
        appLogic.portalFlow.goTo = goTo;
      },
    };
    const defaultProps = {
      claim,
      query: { absence_id: "NTN-111-ABS-01" },
    };

    const options = merge({}, defaultOptions, providedOptions);
    const props = merge({}, defaultProps, providedProps);
    return renderPage(Review, options, props);
  }

  it("redirects if the claim is not reviewable", () => {
    const nonReviewableClaim = baseClaimBuilder
      .eformsV2()
      .reviewable(false)
      .create();

    render(<ReviewWithAppLogic claim={nonReviewableClaim} />);

    expect(goTo).toHaveBeenCalledWith("/employers/applications/status", {
      absence_id: "NTN-111-ABS-01",
    });
  });

  it("renders the page for v1 eforms", () => {
    const { container } = render(
      <ReviewWithAppLogic claim={claimWithV1Eform} />
    );

    expect(
      screen.queryByRole("heading", { name: /Concurrent accrued paid leave/ })
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("heading", { name: /Previous leave/ })
    ).not.toBeInTheDocument();
    expect(
      screen.queryByText(/Please review the benefits listed below/)
    ).toBeInTheDocument();
    expect(container).toMatchSnapshot();
  });

  it("renders the page for v2 eforms", () => {
    const { container } = renderV2Page();

    // existence of Concurrent Leave, Previous Leave sections validated by tests below.
    expect(
      screen.queryByText(
        /Please review the leaves and benefits listed in the tables below/
      )
    ).toBeInTheDocument();
    expect(container).toMatchSnapshot();
  });

  // TODO see if you still need the data-testid changes in ReviewRow.

  describe("within the leave schedule", () => {
    it("shows dates, frequency, and details for continuous leave", () => {
      const continuousLeaveClaim = cloneDeep(claimWithV2Eform);
      delete continuousLeaveClaim.leave_details.reduced_schedule_leave_periods;

      render(<ReviewWithAppLogic claim={continuousLeaveClaim} />);

      const leaveScheduleTable = screen.getByLabelText("Leave schedule");
      expect(leaveScheduleTable.querySelector("tbody")).toMatchSnapshot();
    });

    describe("for reduced leave", () => {
      it("does not show a date range", () => {
        // TODO fix this.
        const reducedLeaveClaim = new MockEmployerClaimBuilder()
          .reducedSchedule()
          .reviewable()
          .eformsV2()
          .create();

        render(<ReviewWithAppLogic claim={reducedLeaveClaim} />);

        const leaveScheduleTable = screen.getByLabelText("Leave schedule");
        const tableRow = leaveScheduleTable.query("tbody > tr");
        screen.debug(tableRow);
      });

      it("shows a notice to contact the call center for details", () => {
        // TODO this.
      });
    });
  });

  describe("within supporting work details", () => {
    it("shows the claimant-submitted weekly hours work", () => {});

    describe("the amendment form", () => {
      it("opens upon clicking 'Amend'", () => {});

      it("allows changing the hours worked per week", () => {});

      it("closes upon clicking 'Cancel amendment'", () => {});

      describe("when there is an error", () => {
        it("automatically opens the amendment form", () => {});

        it("allows closing the amendment form", () => {});
      });
    });
  });

  describe("within 'Previous leave'", () => {});

  describe("within 'Concurrent accrued paid leave'", () => {});

  describe("within 'Employer-sponsored benefits'", () => {});
});
