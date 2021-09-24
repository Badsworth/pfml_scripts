import { render } from "@testing-library/react";
import { MockEmployerClaimBuilder } from "../../../../tests-old/test-utils";
import { Review } from "../../../../src/pages/employers/applications/review";
import User from "../../../../src/models/User";
import { merge } from "lodash";
import useAppLogic from "../../../../src/hooks/useAppLogic";

// TODO delete this test.

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

  it("redirects if the claim is not reviewable", () => {
    const { container } = render(<ReviewWithAppLogic />);
  });
});
