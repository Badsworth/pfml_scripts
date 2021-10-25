import { MockBenefitsApplicationBuilder, renderPage } from "../../test-utils";
import { screen, waitFor } from "@testing-library/react";
import LeaveReason from "../../../src/models/LeaveReason";
import ReducedLeaveSchedule from "../../../src/pages/applications/reduced-leave-schedule";
import { setupBenefitsApplications } from "../../test-utils/helpers";
import userEvent from "@testing-library/user-event";

const setup = ({ claim }) => {
  let updateSpy;

  const utils = renderPage(
    ReducedLeaveSchedule,
    {
      addCustomSetup: (appLogic) => {
        setupBenefitsApplications(appLogic, [claim]);
        updateSpy = jest.spyOn(appLogic.benefitsApplications, "update");
      },
    },
    {
      query: { claim_id: claim.application_id },
    }
  );

  return {
    updateSpy,
    ...utils,
  };
};

describe("ReducedLeaveSchedule", () => {
  it.each([LeaveReason.medical, LeaveReason.pregnancy, LeaveReason.care])(
    "shows text about matching the certification when claim is for %s leave",
    (reason) => {
      const claim = new MockBenefitsApplicationBuilder()
        .reducedSchedule()
        .fixedWorkPattern()
        .create();
      claim.leave_details.reason = reason;

      setup({ claim });

      expect(screen.getByText(/You will need a completed/i)).toMatchSnapshot();
      expect(
        screen.getByText(/The total number of hours you enter must match/i)
      ).toMatchSnapshot();
    }
  );

  describe("when work pattern is a fixed schedule", () => {
    const fixedWorkPatternClaim = new MockBenefitsApplicationBuilder()
      .reducedSchedule()
      .fixedWorkPattern()
      .create();

    it("renders page with 7 fields and full work pattern schedule table", () => {
      setup({ claim: fixedWorkPatternClaim });

      expect(screen.getAllByRole("textbox", { name: "Hours" })).toHaveLength(7);
    });

    it("instructs user to enter 0 for days they won't reduce their hours", () => {
      setup({ claim: fixedWorkPatternClaim });

      expect(
        screen.getByText("Enter 0 for days you won’t work a reduced schedule.")
      ).toBeInTheDocument();
    });

    it("submits the leave_period_id and minutes for each day when the data is manually entered", async () => {
      const { updateSpy } = setup({ claim: fixedWorkPatternClaim });

      screen
        .getAllByRole("textbox", { name: "Hours" })
        .forEach((field, index) => {
          userEvent.clear(field);
          userEvent.type(field, index.toString());
        });

      screen
        .getAllByRole("combobox", {
          name: "Minutes",
        })
        .forEach((field) => {
          userEvent.selectOptions(field, ["0"]);
        });

      userEvent.click(screen.getByRole("button", { name: /save/i }));

      await waitFor(() => expect(updateSpy).toHaveBeenCalled());

      expect(updateSpy).toHaveBeenCalledWith(expect.any(String), {
        leave_details: {
          reduced_schedule_leave_periods: [
            {
              friday_off_minutes: 300,
              leave_period_id: "mock-leave-period-id",
              monday_off_minutes: 60,
              saturday_off_minutes: 360,
              sunday_off_minutes: 0,
              thursday_off_minutes: 240,
              tuesday_off_minutes: 120,
              wednesday_off_minutes: 180,
            },
          ],
        },
      });
    });

    it("submits the leave_period_id and minutes for each day when the data was previously entered", async () => {
      const { updateSpy } = setup({ claim: fixedWorkPatternClaim });
      userEvent.click(screen.getByRole("button", { name: /save/i }));

      await waitFor(() => expect(updateSpy).toHaveBeenCalled());

      expect(updateSpy).toHaveBeenCalledWith(expect.any(String), {
        leave_details: {
          reduced_schedule_leave_periods: [
            {
              // Our mock application builder sets some minute values by default
              friday_off_minutes: 480,
              leave_period_id: "mock-leave-period-id",
              monday_off_minutes: 390,
              saturday_off_minutes: null,
              sunday_off_minutes: null,
              thursday_off_minutes: null,
              tuesday_off_minutes: null,
              wednesday_off_minutes: null,
            },
          ],
        },
      });
    });
  });

  describe("when work pattern is a variable schedule", () => {
    const variableScheduleClaim = new MockBenefitsApplicationBuilder()
      .reducedSchedule()
      .variableWorkPattern()
      .create();

    it("renders page with 1 field", () => {
      setup({ claim: variableScheduleClaim });

      expect(
        screen.getByRole("textbox", { name: "Hours" })
      ).toBeInTheDocument();
    });

    it("submits the leave_period_id and minutes for each day when data is manually entered", async () => {
      const { updateSpy } = setup({ claim: variableScheduleClaim });
      const hoursField = screen.getByRole("textbox", { name: "Hours" });

      userEvent.clear(hoursField);
      userEvent.type(hoursField, "7"); // 7 hours off for the week
      userEvent.selectOptions(
        screen.getByRole("combobox", { name: "Minutes" }),
        ["0"]
      );
      userEvent.click(screen.getByRole("button", { name: /save/i }));

      await waitFor(() => expect(updateSpy).toHaveBeenCalled());

      expect(updateSpy).toHaveBeenCalledWith(expect.any(String), {
        leave_details: {
          reduced_schedule_leave_periods: [
            {
              // 7 hours gets distributed across each day
              friday_off_minutes: 60,
              leave_period_id: "mock-leave-period-id",
              monday_off_minutes: 60,
              saturday_off_minutes: 60,
              sunday_off_minutes: 60,
              thursday_off_minutes: 60,
              tuesday_off_minutes: 60,
              wednesday_off_minutes: 60,
            },
          ],
        },
      });
    });

    it("submits empty daily values when no answers were provided", async () => {
      const claim = new MockBenefitsApplicationBuilder()
        .reducedSchedule()
        .variableWorkPattern()
        .create();
      // Clear defaults set by the mock builder
      claim.leave_details.reduced_schedule_leave_periods[0].monday_off_minutes =
        null;
      claim.leave_details.reduced_schedule_leave_periods[0].friday_off_minutes =
        null;

      const { updateSpy } = setup({ claim });

      userEvent.click(screen.getByRole("button", { name: /save/i }));

      await waitFor(() => expect(updateSpy).toHaveBeenCalled());

      expect(updateSpy).toHaveBeenCalledWith(expect.any(String), {
        leave_details: {
          reduced_schedule_leave_periods: [
            {
              friday_off_minutes: null,
              leave_period_id: "mock-leave-period-id",
              monday_off_minutes: null,
              saturday_off_minutes: null,
              sunday_off_minutes: null,
              thursday_off_minutes: null,
              tuesday_off_minutes: null,
              wednesday_off_minutes: null,
            },
          ],
        },
      });
    });
  });
});
