import { MockClaimBuilder, renderWithAppLogic } from "../../test-utils";
import LeaveDates from "../../../src/pages/claims/leave-dates";

jest.mock("../../../src/hooks/useAppLogic");

describe("LeaveDates", () => {
  let appLogic, claim, wrapper;

  function render() {
    ({ appLogic, wrapper } = renderWithAppLogic(LeaveDates, {
      claimAttrs: claim,
    }));
  }

  it("renders the page", () => {
    claim = new MockClaimBuilder().medicalLeaveReason().create();
    render();
    expect(wrapper).toMatchSnapshot();
  });

  describe("when leave type is bonding", () => {
    it("shows the bonding leave question text", () => {
      claim = new MockClaimBuilder().bondingBirthLeaveReason().create();
      render();
      expect(
        wrapper.find({
          name: "leave_details.continuous_leave_periods[0].start_date",
        })
      ).toMatchSnapshot();
      expect(
        wrapper.find({
          name: "leave_details.continuous_leave_periods[0].end_date",
        })
      ).toMatchSnapshot();
    });
  });

  it("sends continuous leave dates to the api", () => {
    claim = new MockClaimBuilder().continuous().create();
    const {
      end_date,
      start_date,
    } = claim.leave_details.continuous_leave_periods[0];

    render();
    wrapper.find("QuestionPage").simulate("save");

    expect(appLogic.claims.update).toHaveBeenCalledWith(claim.application_id, {
      leave_details: {
        continuous_leave_periods: [{ end_date, start_date }],
      },
    });
  });

  it.todo("includes existing leave_period_id in subsequent API requests");
});
