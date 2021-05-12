import {
  MockBenefitsApplicationBuilder,
  renderWithAppLogic,
  simulateEvents,
} from "../../test-utils";
import ReducedLeaveSchedule from "../../../src/pages/applications/reduced-leave-schedule";

jest.mock("../../../src/hooks/useAppLogic");

const fixedWorkPatternClaim = new MockBenefitsApplicationBuilder()
  .reducedSchedule()
  .fixedWorkPattern()
  .create();

const variableScheduleClaim = new MockBenefitsApplicationBuilder()
  .reducedSchedule()
  .variableWorkPattern()
  .create();

const setup = (claimAttrs) => {
  const { appLogic, claim, wrapper } = renderWithAppLogic(
    ReducedLeaveSchedule,
    {
      claimAttrs,
    }
  );

  const { changeField, submitForm } = simulateEvents(wrapper);

  return {
    appLogic,
    claim,
    changeField,
    submitForm,
    wrapper,
  };
};

describe("ReducedLeaveSchedule", () => {
  it("renders lead with expected content when leave reason is Medical", () => {
    const claim = new MockBenefitsApplicationBuilder()
      .medicalLeaveReason()
      .reducedSchedule()
      .variableWorkPattern()
      .create();

    const { wrapper } = setup(claim);
    expect(wrapper.find("Lead").find("Trans").dive()).toMatchSnapshot();
  });

  it("renders lead with expected content when leave reason is Bonding", () => {
    const claim = new MockBenefitsApplicationBuilder()
      .bondingBirthLeaveReason()
      .reducedSchedule()
      .variableWorkPattern()
      .create();

    const { wrapper } = setup(claim);

    expect(wrapper.find("Lead").find("Trans").dive()).toMatchSnapshot();
  });

  describe("when work pattern is a fixed schedule", () => {
    it("renders section label with expected content", () => {
      const { wrapper } = setup(fixedWorkPatternClaim);

      expect(wrapper.find("Heading")).toMatchSnapshot();
    });

    it("renders the WeeklyTimeTable with the work schedule", () => {
      const { claim, wrapper } = setup(fixedWorkPatternClaim);

      const details = wrapper.find("Details");
      const table = wrapper.find("WeeklyTimeTable");

      expect(details.prop("label")).toMatchInlineSnapshot(
        `"View your work schedule"`
      );
      expect(table.prop("weeks")).toEqual(claim.work_pattern.weeks);
    });

    it("renders the page with an input for each day", () => {
      const { wrapper } = setup(fixedWorkPatternClaim);

      const inputs = wrapper.find("InputHours");

      expect(inputs).toHaveLength(7);
      expect(inputs).toMatchSnapshot();
    });

    it("submits the leave_period_id and minutes for each day when the data is manually entered", () => {
      const { appLogic, changeField, claim, submitForm } = setup(
        fixedWorkPatternClaim
      );

      changeField(
        "leave_details.reduced_schedule_leave_periods[0].monday_off_minutes",
        480
      );
      changeField(
        "leave_details.reduced_schedule_leave_periods[0].friday_off_minutes",
        480
      );

      submitForm();

      expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
        claim.application_id,
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

    it("submits the leave_period_id and minutes for each day when the data was previously entered", () => {
      const claimWithHours = Object.assign({}, fixedWorkPatternClaim);
      claimWithHours.leave_details.reduced_schedule_leave_periods[0].monday_off_minutes = 480;
      claimWithHours.leave_details.reduced_schedule_leave_periods[0].friday_off_minutes = 480;

      const { appLogic, claim, submitForm } = setup(claimWithHours);

      submitForm();

      expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
        claim.application_id,
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
    it("renders section label with expected content", () => {
      const { wrapper } = setup(variableScheduleClaim);

      expect(wrapper.find("Heading")).toMatchSnapshot();
    });

    it("renders the work schedule as a weekly average", () => {
      const { wrapper } = setup(variableScheduleClaim);

      expect(wrapper.find("Details")).toMatchInlineSnapshot(`
        <Details
          label="View your work schedule"
        >
          40h
        </Details>
      `);
    });

    it("renders a single field for gathering the schedule", () => {
      const { wrapper } = setup(variableScheduleClaim);

      const inputs = wrapper.find("InputHours");

      expect(inputs).toHaveLength(1);
      expect(inputs).toMatchSnapshot();
    });

    it("submits the leave_period_id and minutes for each day when data is manually entered", () => {
      const { appLogic, changeField, claim, wrapper } = setup(
        variableScheduleClaim
      );

      changeField("totalMinutesOff", 480);

      wrapper.find("QuestionPage").simulate("save");

      expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
        claim.application_id,
        {
          leave_details: {
            reduced_schedule_leave_periods: [
              {
                friday_off_minutes: 60,
                leave_period_id: "mock-leave-period-id",
                monday_off_minutes: 75,
                saturday_off_minutes: 60,
                sunday_off_minutes: 75,
                thursday_off_minutes: 60,
                tuesday_off_minutes: 75,
                wednesday_off_minutes: 75,
              },
            ],
          },
        }
      );
    });

    it("submits the leave_period_id and minutes for each day when data was previously entered", () => {
      const leave_details = {
        reduced_schedule_leave_periods: [
          {
            friday_off_minutes: 60,
            leave_period_id: "mock-leave-period-id",
            monday_off_minutes: 75,
            saturday_off_minutes: 60,
            sunday_off_minutes: 75,
            thursday_off_minutes: 60,
            tuesday_off_minutes: 75,
            wednesday_off_minutes: 75,
          },
        ],
      };

      const claimWithMinutes = Object.assign({}, variableScheduleClaim);
      claimWithMinutes.leave_details = leave_details;

      const { appLogic, changeField, claim, wrapper } = setup(claimWithMinutes);

      changeField("totalMinutesOff", 480);

      wrapper.find("QuestionPage").simulate("save");

      expect(appLogic.benefitsApplications.update).toHaveBeenCalledWith(
        claim.application_id,
        {
          leave_details,
        }
      );
    });
  });
});
