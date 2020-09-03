import {
  MockClaimBuilder,
  renderWithAppLogic,
  simulateEvents,
} from "../../test-utils";
import LeaveDates from "../../../src/pages/claims/leave-dates";
import { act } from "react-dom/test-utils";

jest.mock("../../../src/hooks/useAppLogic");

describe("LeaveDates", () => {
  const end_date = "2020-08-28";
  const start_date = "2020-07-27";
  let appLogic, changeField, claim, wrapper;

  function render() {
    ({ appLogic, wrapper } = renderWithAppLogic(LeaveDates, {
      claimAttrs: claim,
    }));
    ({ changeField } = simulateEvents(wrapper));
  }

  function fillFormAndSave() {
    changeField("temp.leave_details.start_date", start_date);
    changeField("temp.leave_details.end_date", end_date);
    act(() => {
      wrapper.find("QuestionPage").simulate("save");
    });
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
        wrapper.find({ name: "temp.leave_details.start_date" })
      ).toMatchSnapshot();
      expect(
        wrapper.find({ name: "temp.leave_details.end_date" })
      ).toMatchSnapshot();
    });
  });

  // TODO (CP-724): Look into updating the API interface to accept a single leave_details object rather than
  // separate objects for continuous / intermittent / reduced schedule leave types.
  describe("API integration", () => {
    const leave_period_id = "mock-leave-period-id";

    it("sends continuous leave dates to the api", () => {
      claim = new MockClaimBuilder().continuous({ leave_period_id }).create();
      render();
      fillFormAndSave();

      expect(appLogic.claims.update).toHaveBeenCalledWith(
        claim.application_id,
        {
          leave_details: {
            continuous_leave_periods: [
              { leave_period_id, end_date, start_date },
            ],
          },
          temp: { leave_details: { end_date, start_date } },
        }
      );
    });

    it("sends intermittent leave dates to the api", () => {
      claim = new MockClaimBuilder().intermittent({ leave_period_id }).create();
      render();
      fillFormAndSave();

      expect(appLogic.claims.update).toHaveBeenCalledWith(
        claim.application_id,
        {
          leave_details: {
            intermittent_leave_periods: [
              expect.objectContaining({
                leave_period_id,
                end_date,
                start_date,
              }),
            ],
          },
          temp: { leave_details: { end_date, start_date } },
        }
      );
    });

    it("sends reduced schedule leave dates to the api", () => {
      claim = new MockClaimBuilder()
        .reducedSchedule({ leave_period_id })
        .create();
      render();
      fillFormAndSave();

      expect(appLogic.claims.update).toHaveBeenCalledWith(
        claim.application_id,
        {
          leave_details: {
            reduced_schedule_leave_periods: [
              { leave_period_id, end_date, start_date },
            ],
          },
          temp: { leave_details: { end_date, start_date } },
        }
      );
    });

    it("sends multiple leave schedule leave dates to the api", () => {
      claim = new MockClaimBuilder()
        .continuous({ leave_period_id })
        .intermittent({ leave_period_id })
        .reducedSchedule({ leave_period_id })
        .create();
      render();
      fillFormAndSave();

      expect(appLogic.claims.update).toHaveBeenCalledWith(
        claim.application_id,
        {
          leave_details: {
            continuous_leave_periods: [
              { leave_period_id, end_date, start_date },
            ],
            intermittent_leave_periods: [
              expect.objectContaining({
                leave_period_id,
                end_date,
                start_date,
              }),
            ],
            reduced_schedule_leave_periods: [
              { leave_period_id, end_date, start_date },
            ],
          },
          temp: { leave_details: { end_date, start_date } },
        }
      );
    });
  });
});
