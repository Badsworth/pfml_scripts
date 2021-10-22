import { MockBenefitsApplicationBuilder, renderPage } from "../../test-utils";
import {
  WorkPattern,
  WorkPatternType,
} from "../../../src/models/BenefitsApplication";
import { screen, waitFor } from "@testing-library/react";
import ScheduleFixed from "../../../src/pages/applications/schedule-fixed";
import { setupBenefitsApplications } from "../../test-utils/helpers";
import userEvent from "@testing-library/user-event";

const MINUTES_WORKED_PER_WEEK = 60 * 8 * 7;

const defaultClaim = new MockBenefitsApplicationBuilder()
  .continuous()
  .workPattern({
    work_pattern_type: WorkPatternType.fixed,
  })
  .create();

const updateClaim = jest.fn(() => {
  return Promise.resolve();
});

const setup = (claim = defaultClaim) => {
  return renderPage(
    ScheduleFixed,
    {
      addCustomSetup: (appLogic) => {
        setupBenefitsApplications(appLogic, [claim]);
        appLogic.benefitsApplications.update = updateClaim;
      },
    },
    { query: { claim_id: "mock_application_id" } }
  );
};

describe("ScheduleFixed", () => {
  it("renders the page", () => {
    const { container } = setup();
    expect(container).toMatchSnapshot();
  });

  it("displays work schedule values that were previously entered", () => {
    const workPattern = WorkPattern.createWithWeek(MINUTES_WORKED_PER_WEEK);
    const claim = new MockBenefitsApplicationBuilder()
      .continuous()
      .workPattern({
        work_pattern_type: WorkPatternType.fixed,
        work_pattern_days: workPattern.work_pattern_days,
      })
      .create();
    setup(claim);

    const hoursInputs = screen.getAllByRole("textbox", { name: "Hours" });
    hoursInputs.forEach((input) => {
      expect(input).toHaveValue("8");
    });
  });

  it("updates the claim's work_pattern_days and hours_worked_per_week when the page is submitted", async () => {
    setup();

    const hoursInputs = screen.getAllByRole("textbox", { name: "Hours" });
    hoursInputs.forEach((input) => {
      userEvent.type(input, "1");
    });

    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));

    await waitFor(() => {
      expect(updateClaim).toHaveBeenCalledWith(
        "mock_application_id",
        expect.objectContaining({
          hours_worked_per_week: 7,
          work_pattern: {
            work_pattern_days: [
              { day_of_week: "Sunday", minutes: 60 },
              { day_of_week: "Monday", minutes: 60 },
              { day_of_week: "Tuesday", minutes: 60 },
              { day_of_week: "Wednesday", minutes: 60 },
              { day_of_week: "Thursday", minutes: 60 },
              { day_of_week: "Friday", minutes: 60 },
              { day_of_week: "Saturday", minutes: 60 },
            ],
          },
        })
      );
    });
  });
});
