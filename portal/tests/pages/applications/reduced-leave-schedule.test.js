import {
  MockClaimBuilder,
  renderWithAppLogic,
  simulateEvents,
} from "../../test-utils";
import ReducedLeaveSchedule from "../../../src/pages/applications/reduced-leave-schedule";

jest.mock("../../../src/hooks/useAppLogic");

describe("ReducedLeaveSchedule", () => {
  let mockClaim;

  describe("when leave reason is Medical", () => {
    it("renders lead with expected content", () => {
      const { wrapper } = renderWithAppLogic(ReducedLeaveSchedule, {
        claimAttrs: new MockClaimBuilder()
          .medicalLeaveReason()
          .reducedSchedule()
          .variableWorkPattern()
          .create(),
      });

      expect(wrapper.find("Lead").find("Trans").dive()).toMatchSnapshot();
    });
  });

  describe("when leave reason is Bonding", () => {
    it("renders lead with expected content", () => {
      const { wrapper } = renderWithAppLogic(ReducedLeaveSchedule, {
        claimAttrs: new MockClaimBuilder()
          .bondingBirthLeaveReason()
          .reducedSchedule()
          .variableWorkPattern()
          .create(),
      });

      expect(wrapper.find("Lead").find("Trans").dive()).toMatchSnapshot();
    });
  });

  describe("when work pattern is a fixed schedule", () => {
    beforeEach(() => {
      mockClaim = new MockClaimBuilder()
        .reducedSchedule()
        .fixedWorkPattern()
        .create();
    });

    it("renders section label with expected content", () => {
      const { wrapper } = renderWithAppLogic(ReducedLeaveSchedule, {
        claimAttrs: mockClaim,
      });

      expect(wrapper.find("Heading")).toMatchSnapshot();
    });

    it("renders the WeeklyTimeTable with the work schedule", () => {
      const { wrapper } = renderWithAppLogic(ReducedLeaveSchedule, {
        claimAttrs: mockClaim,
      });

      const details = wrapper.find("Details");
      const table = wrapper.find("WeeklyTimeTable");

      expect(details.prop("label")).toMatchInlineSnapshot(
        `"View your work schedule"`
      );
      expect(table.prop("weeks")).toEqual(mockClaim.work_pattern.weeks);
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

  describe("when work pattern is a variable schedule", () => {
    beforeEach(() => {
      mockClaim = new MockClaimBuilder()
        .reducedSchedule()
        .variableWorkPattern()
        .create();
    });

    it("renders section label with expected content", () => {
      const { wrapper } = renderWithAppLogic(ReducedLeaveSchedule, {
        claimAttrs: mockClaim,
      });

      expect(wrapper.find("Heading")).toMatchSnapshot();
    });

    it("renders the work schedule as a weekly average", () => {
      const { wrapper } = renderWithAppLogic(ReducedLeaveSchedule, {
        claimAttrs: mockClaim,
      });

      expect(wrapper.find("Details")).toMatchInlineSnapshot(`
        <Details
          label="View your work schedule"
        >
          40h
        </Details>
      `);
    });

    it("renders a single field for gathering the schedule", () => {
      const { wrapper } = renderWithAppLogic(ReducedLeaveSchedule, {
        claimAttrs: mockClaim,
      });

      const inputs = wrapper.find("InputHours");

      expect(inputs).toHaveLength(1);
      expect(inputs).toMatchSnapshot();
    });

    it("submits the leave_period_id and minutes for each day", () => {
      const { appLogic, wrapper } = renderWithAppLogic(ReducedLeaveSchedule, {
        claimAttrs: mockClaim,
      });

      const { changeField } = simulateEvents(wrapper);

      changeField("totalMinutesOff", 480);

      wrapper.find("QuestionPage").simulate("save");

      expect(appLogic.claims.update).toHaveBeenCalledWith(
        mockClaim.application_id,
        {
          leave_details: {
            reduced_schedule_leave_periods: [
              {
                friday_off_minutes: 68,
                leave_period_id: "mock-leave-period-id",
                monday_off_minutes: 69,
                saturday_off_minutes: 68,
                sunday_off_minutes: 69,
                thursday_off_minutes: 68,
                tuesday_off_minutes: 69,
                wednesday_off_minutes: 69,
              },
            ],
          },
        }
      );
    });
  });
});
