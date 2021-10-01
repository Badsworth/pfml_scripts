import {
  DayOfWeek,
  WorkPattern,
  WorkPatternDay,
  WorkPatternType,
} from "../../../src/models/BenefitsApplication";
import { MockBenefitsApplicationBuilder, renderPage } from "../../test-utils";
import { screen, waitFor } from "@testing-library/react";

import ScheduleVariable from "../../../src/pages/applications/schedule-variable";
import { setupBenefitsApplications } from "../../test-utils/helpers";
import userEvent from "@testing-library/user-event";

const defaultClaim = new MockBenefitsApplicationBuilder()
  .continuous()
  .workPattern({
    work_pattern_days: [],
    work_pattern_type: WorkPatternType.variable,
  })
  .create();

const updateClaim = jest.fn(() => {
  return Promise.resolve();
});
const setup = (claim = defaultClaim) => {
  return renderPage(
    ScheduleVariable,
    {
      addCustomSetup: (appLogic) => {
        setupBenefitsApplications(appLogic, [claim]);
        appLogic.benefitsApplications.update = updateClaim;
      },
    },
    { query: { claim_id: "mock_application_id" } }
  );
};

describe("ScheduleVariable", () => {
  it("renders the form", () => {
    const { container } = setup();
    expect(container).toMatchSnapshot();
  });

  it("submits hours_worked_per_week and 7 day work pattern when entering hours for the first time", async () => {
    setup();
    userEvent.type(screen.getByRole("textbox", { name: "Hours" }), "7");
    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));

    await waitFor(() => {
      expect(updateClaim).toHaveBeenCalledWith(defaultClaim.application_id, {
        hours_worked_per_week: 7,
        work_pattern: {
          work_pattern_days: Object.values(DayOfWeek).map(
            (day_of_week) => new WorkPatternDay({ day_of_week, minutes: 60 })
          ),
        },
      });
    });
  });

  it("submits updated data when user changes their answer", async () => {
    const initialWorkPattern = WorkPattern.createWithWeek(60 * 7); // 1 hour each day
    setup(
      new MockBenefitsApplicationBuilder()
        .continuous()
        .workPattern({
          work_pattern_days: initialWorkPattern.work_pattern_days,
          work_pattern_type: WorkPatternType.variable,
        })
        .create()
    );

    userEvent.type(
      screen.getByRole("textbox", { name: "Hours" }),
      "{backspace}14"
    );
    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));

    await waitFor(() => {
      expect(updateClaim).toHaveBeenCalledWith("mock_application_id", {
        hours_worked_per_week: 14,
        work_pattern: {
          work_pattern_days: Object.values(DayOfWeek).map(
            (day_of_week) => new WorkPatternDay({ day_of_week, minutes: 120 })
          ),
        },
      });
    });
  });

  it("clears the form when the user clears their input", async () => {
    const initialWorkPattern = WorkPattern.createWithWeek(60 * 7); // 1 hour each day
    setup(
      new MockBenefitsApplicationBuilder()
        .continuous()
        .workPattern({
          work_pattern_days: initialWorkPattern.work_pattern_days,
          work_pattern_type: WorkPatternType.variable,
        })
        .create()
    );
    userEvent.type(
      screen.getByRole("textbox", { name: "Hours" }),
      "{backspace}"
    );
    userEvent.selectOptions(screen.getByRole("combobox", { name: "Minutes" }), [
      "",
    ]);
    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));
    await waitFor(() => {
      expect(updateClaim).toHaveBeenCalledWith("mock_application_id", {
        hours_worked_per_week: null,
        work_pattern: {
          work_pattern_days: [],
        },
      });
    });
  });

  it("submits data when user doesn't change their answers", async () => {
    const initialWorkPattern = WorkPattern.createWithWeek(60 * 7); // 1 hour each day
    setup(
      new MockBenefitsApplicationBuilder()
        .continuous()
        .workPattern({
          work_pattern_days: initialWorkPattern.work_pattern_days,
          work_pattern_type: WorkPatternType.variable,
        })
        .create()
    );

    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));
    await waitFor(() => {
      expect(updateClaim).toHaveBeenCalledWith("mock_application_id", {
        hours_worked_per_week: 7,
        work_pattern: {
          work_pattern_days: Object.values(DayOfWeek).map(
            (day_of_week) => new WorkPatternDay({ day_of_week, minutes: 60 })
          ),
        },
      });
    });
  });

  it("creates a blank work pattern when user doesn't enter a time amount", async () => {
    setup();

    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));
    await waitFor(() => {
      expect(updateClaim).toHaveBeenCalledWith(defaultClaim.application_id, {
        hours_worked_per_week: null,
        work_pattern: {
          work_pattern_days: [],
        },
      });
    });
  });
});
