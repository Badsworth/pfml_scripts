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
    render();
    expect(wrapper).toMatchSnapshot();
  });

  // TODO (CP-724): Look into updating the API interface to accept a single leave_details object rather than
  // separate objects for continuous / intermittent / reduced schedule leave types.
  describe("API integration", () => {
    it("sends continuous leave dates to the api", () => {
      claim = new MockClaimBuilder().continuous().create();
      render();
      fillFormAndSave();

      expect(appLogic.claims.update).toHaveBeenCalledWith(
        claim.application_id,
        {
          leave_details: {
            continuous_leave_periods: [{ end_date, start_date }],
          },
          temp: { leave_details: { end_date, start_date } },
        }
      );
    });

    it("sends intermittent leave dates to the api", () => {
      claim = new MockClaimBuilder().intermittent().create();
      render();
      fillFormAndSave();

      expect(appLogic.claims.update).toHaveBeenCalledWith(
        claim.application_id,
        {
          leave_details: {
            intermittent_leave_periods: [{ end_date, start_date }],
          },
          temp: { leave_details: { end_date, start_date } },
        }
      );
    });

    it("sends reduced schedule leave dates to the api", () => {
      claim = new MockClaimBuilder().reducedSchedule().create();
      render();
      fillFormAndSave();

      expect(appLogic.claims.update).toHaveBeenCalledWith(
        claim.application_id,
        {
          leave_details: {
            reduced_schedule_leave_periods: [{ end_date, start_date }],
          },
          temp: { leave_details: { end_date, start_date } },
        }
      );
    });

    it("sends multiple leave schedule leave dates to the api", () => {
      claim = new MockClaimBuilder()
        .continuous()
        .intermittent()
        .reducedSchedule()
        .create();
      render();
      fillFormAndSave();

      expect(appLogic.claims.update).toHaveBeenCalledWith(
        claim.application_id,
        {
          leave_details: {
            continuous_leave_periods: [{ end_date, start_date }],
            intermittent_leave_periods: [{ end_date, start_date }],
            reduced_schedule_leave_periods: [{ end_date, start_date }],
          },
          temp: { leave_details: { end_date, start_date } },
        }
      );
    });
  });
});
