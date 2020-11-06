import {
  MockClaimBuilder,
  renderWithAppLogic,
  simulateEvents,
} from "../../test-utils";
import { WorkPattern, WorkPatternType } from "../../../src/models/Claim";
import ReducedLeaveSchedule from "../../../src/pages/claims/reduced-leave-schedule";

jest.mock("../../../src/hooks/useAppLogic");

describe("ReducedLeaveSchedule", () => {
  let mockClaim;

  describe("when work pattern is a fixed schedule", () => {
    beforeEach(() => {
      const workPattern = WorkPattern.addWeek(
        new WorkPattern(),
        // 8 hours days for 7 days
        8 * 60 * 7
      );
      mockClaim = new MockClaimBuilder()
        .reducedSchedule()
        .workPattern({
          work_pattern_type: WorkPatternType.fixed,
          work_pattern_days: workPattern.work_pattern_days,
        })
        .create();
    });

    it("renders the WorkPatternTable with the work schedule", () => {
      const { wrapper } = renderWithAppLogic(ReducedLeaveSchedule, {
        claimAttrs: mockClaim,
      });

      const details = wrapper.find("Details");
      const table = wrapper.find("WorkPatternTable");

      expect(details.prop("label")).toMatchInlineSnapshot(
        `"View your work schedule"`
      );
      expect(table.prop("weeks")).toEqual(
        new WorkPattern(mockClaim.work_pattern).weeks
      );
    });

    it("renders the page with an input for each day", () => {
      const { wrapper } = renderWithAppLogic(ReducedLeaveSchedule, {
        claimAttrs: mockClaim,
      });

      const inputs = wrapper.find("InputHours");

      expect(inputs).toHaveLength(7);
      expect(inputs).toMatchSnapshot();
    });

    it("submits the leave_period_id and minutes for each day", () => {
      const { appLogic, wrapper } = renderWithAppLogic(ReducedLeaveSchedule, {
        claimAttrs: mockClaim,
      });

      const { changeField } = simulateEvents(wrapper);

      changeField(
        "leave_details.reduced_schedule_leave_periods[0].monday_off_minutes",
        480
      );
      changeField(
        "leave_details.reduced_schedule_leave_periods[0].friday_off_minutes",
        480
      );

      wrapper.find("QuestionPage").simulate("save");

      expect(appLogic.claims.update).toHaveBeenCalledWith(
        mockClaim.application_id,
        {
          leave_details: {
            reduced_schedule_leave_periods: [
              {
                friday_off_minutes: 480,
                leave_period_id: "mock-leave-period-id",
                monday_off_minutes: 480,
                saturday_off_minutes: null,
                sunday_off_minutes: null,
                thursday_off_minutes: null,
                tuesday_off_minutes: null,
                wednesday_off_minutes: null,
              },
            ],
          },
        }
      );
    });
  });
});
