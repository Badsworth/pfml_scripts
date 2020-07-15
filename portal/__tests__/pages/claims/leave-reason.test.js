import { LeaveReason } from "../../../src/models/Claim";
import LeaveReasonPage from "../../../src/pages/claims/leave-reason";
import { renderWithAppLogic } from "../../test-utils";

describe("LeaveReasonPage", () => {
  it("renders the page", () => {
    const { wrapper } = renderWithAppLogic(LeaveReasonPage, {
      claimAttrs: {
        leave_details: {
          reason: LeaveReason.medical,
        },
      },
    });

    expect(wrapper).toMatchSnapshot();
  });
});
