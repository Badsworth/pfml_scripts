import Document, { DocumentType } from "../../../../src/models/Document";
import DocumentCollection from "../../../../src/models/DocumentCollection";
import LeaveReason from "../../../../src/models/LeaveReason";
import { Review } from "../../../../src/pages/employers/applications/review";
import { MockEmployerClaimBuilder } from "../../../../tests-old/test-utils";
import { renderPage } from "../../../test-utils";
import { render, screen } from "@testing-library/react";
import { merge } from "lodash";
import useAppLogic from "../../../../src/hooks/useAppLogic";
import User from "../../../../src/models/User";

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

describe("Review", () => {
  const goTo = jest.fn();
  const baseClaimBuilder = new MockEmployerClaimBuilder()
    .completed()
    .reviewable();
  const claimWithV1Eform = baseClaimBuilder.eformsV1().create();
  const claimWithV2Eform = baseClaimBuilder.eformsV2().create();
  const query = { absence_id: "NTN-111-ABS-01" };

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

  it.only("redirects if the claim is not reviewable", async () => {
    const nonReviewableClaim = baseClaimBuilder
      .eformsV2()
      .reviewable(false)
      .create();

    render(<ReviewWithAppLogic claim={nonReviewableClaim} />);
    // renderV2Page({}, { claim: nonReviewableClaim });

    expect(goTo).toHaveBeenCalledTimes(1);
    expect(goTo).toHaveBeenCalledWith("/employers/applications/status", {
      absence_id: "NTN-111-ABS-01",
    });
  });

  it("renders the page for v1 eforms", () => {
    const { container } = renderPage(
      Review,
      {
        addCustomSetup: (appLogic) => {
          appLogic.employers.claim = claimWithV1Eform;
        },
      },
      {
        claim: claimWithV1Eform,
        query,
      }
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

  describe("displays organization/employer information", () => {
    const { container } = renderV2Page();
    const organizationRow = screen.queryByTestId("org-name-row");
    const einRow = screen.queryByTestId("ein-row");
  });
});
