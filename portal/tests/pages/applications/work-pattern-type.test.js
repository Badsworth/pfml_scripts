import { MockBenefitsApplicationBuilder, renderPage } from "../../test-utils";
import { screen, waitFor } from "@testing-library/react";
import WorkPatternType from "../../../src/pages/applications/work-pattern-type";
import { WorkPatternType as WorkPatternTypeEnum } from "../../../src/models/BenefitsApplication";
import { setupBenefitsApplications } from "../../test-utils/helpers";
import userEvent from "@testing-library/user-event";

const updateClaim = jest.fn(() => {
  return Promise.resolve();
});

const setup = (claim) => {
  if (!claim) {
    claim = new MockBenefitsApplicationBuilder().create();
  }
  return renderPage(
    WorkPatternType,
    {
      addCustomSetup: (appLogicHook) => {
        setupBenefitsApplications(appLogicHook, [claim]);
        appLogicHook.benefitsApplications.update = updateClaim;
      },
    },
    { query: { claim_id: "mock_application_id" } }
  );
};

describe("WorkPatternType", () => {
  it("renders the page with expected content", () => {
    const { container } = setup();
    expect(container).toMatchSnapshot();
  });

  it("resets hours_worked_per_week to null and work_pattern_days to empty array when type changes", async () => {
    setup(new MockBenefitsApplicationBuilder().fixedWorkPattern().create());
    userEvent.click(
      screen.getByRole("radio", {
        name: "My schedule is not consistent from week to week. For example, I work 40 hours every week but the days differ, or my schedule changes from week to week.",
      })
    );

    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));
    await waitFor(() => {
      expect(updateClaim).toHaveBeenCalledWith("mock_application_id", {
        hours_worked_per_week: null,
        work_pattern: {
          work_pattern_days: [],
          work_pattern_type: WorkPatternTypeEnum.variable,
        },
      });
    });
  });

  it("does not reset hours_worked_per_week to null and work_pattern_days to empty array when type does NOT change", async () => {
    setup(new MockBenefitsApplicationBuilder().fixedWorkPattern().create());

    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));
    await waitFor(() => {
      expect(updateClaim).toHaveBeenCalledWith("mock_application_id", {
        work_pattern: {
          work_pattern_type: WorkPatternTypeEnum.fixed,
        },
      });
    });
  });
});
