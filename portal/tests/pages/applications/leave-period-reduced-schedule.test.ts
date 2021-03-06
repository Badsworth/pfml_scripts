import { MockBenefitsApplicationBuilder, renderPage } from "../../test-utils";
import { screen, waitFor, within } from "@testing-library/react";
import BenefitsApplication from "../../../src/models/BenefitsApplication";
import LeavePeriodReducedSchedule from "../../../src/pages/applications/leave-period-reduced-schedule";
import { setupBenefitsApplications } from "../../test-utils/helpers";
import userEvent from "@testing-library/user-event";

function setup({ claim }: { claim: BenefitsApplication }) {
  const updateSpy = jest.fn();

  const utils = renderPage(
    LeavePeriodReducedSchedule,
    {
      addCustomSetup: (appLogic) => {
        setupBenefitsApplications(appLogic, [claim]);
        appLogic.benefitsApplications.update = updateSpy;
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
}

describe("LeavePeriodReducedSchedule", () => {
  it.each([
    ["bonding", new MockBenefitsApplicationBuilder().bondingBirthLeaveReason()],
    ["caring", new MockBenefitsApplicationBuilder().caringLeaveReason()],
    ["medical", new MockBenefitsApplicationBuilder().medicalLeaveReason()],
    ["pregnancy", new MockBenefitsApplicationBuilder().pregnancyLeaveReason()],
  ])(
    "renders a variation of the page when claimant is taking %s leave",
    (_type, claim) => {
      const { container } = setup({
        claim: claim.create(),
      });

      expect(container).toMatchSnapshot();
    }
  );

  it("adds empty leave period when user first indicates they have this leave period", async () => {
    const claim = new MockBenefitsApplicationBuilder()
      .medicalLeaveReason()
      .create();

    const { updateSpy } = setup({ claim });

    userEvent.click(screen.getByRole("radio", { name: /yes/i }));
    userEvent.click(screen.getByRole("button", { name: /save/i }));

    await waitFor(() => {
      expect(updateSpy).toHaveBeenCalledWith(claim.application_id, {
        has_reduced_schedule_leave_periods: true,
        leave_details: {
          reduced_schedule_leave_periods: [{}],
        },
      });
    });
  });

  it("submits form successfully with pre-filled data", async () => {
    const claim = new MockBenefitsApplicationBuilder()
      .reducedSchedule()
      .create();
    const { end_date, start_date, leave_period_id } =
      claim.leave_details.reduced_schedule_leave_periods[0];

    const { updateSpy } = setup({ claim });

    userEvent.click(screen.getByRole("button", { name: /save/i }));

    await waitFor(() => {
      expect(updateSpy).toHaveBeenCalledWith(claim.application_id, {
        has_reduced_schedule_leave_periods: true,
        leave_details: {
          reduced_schedule_leave_periods: [
            { end_date, start_date, leave_period_id },
          ],
        },
      });
    });
  });

  it("removes leave periods data when changing answer from Yes to No", async () => {
    const claim = new MockBenefitsApplicationBuilder()
      .reducedSchedule()
      .create();
    const { updateSpy } = setup({ claim });

    userEvent.click(screen.getByRole("radio", { name: /no/i }));
    userEvent.click(screen.getByRole("button", { name: /save/i }));

    await waitFor(() => {
      expect(updateSpy).toHaveBeenCalledWith(claim.application_id, {
        has_reduced_schedule_leave_periods: false,
        leave_details: {
          reduced_schedule_leave_periods: null,
        },
      });
    });
  });

  it("sends reduced leave dates and ID to the api when the user enters leave data", async () => {
    const claim = new MockBenefitsApplicationBuilder()
      .bondingBirthLeaveReason()
      .create();
    const { updateSpy } = setup({ claim });

    userEvent.click(screen.getByRole("radio", { name: /yes/i }));

    const startDateGroup = screen.getByRole("group", { name: /first day/i });
    const endDateGroup = screen.getByRole("group", { name: /last day/i });

    userEvent.type(
      within(startDateGroup).getByRole("textbox", { name: /month/i }),
      "1"
    );
    userEvent.type(
      within(startDateGroup).getByRole("textbox", { name: /day/i }),
      "30"
    );
    userEvent.type(
      within(startDateGroup).getByRole("textbox", { name: /year/i }),
      "2021"
    );

    userEvent.type(
      within(endDateGroup).getByRole("textbox", { name: /month/i }),
      "3"
    );
    userEvent.type(
      within(endDateGroup).getByRole("textbox", { name: /day/i }),
      "29"
    );
    userEvent.type(
      within(endDateGroup).getByRole("textbox", { name: /year/i }),
      "2021"
    );

    userEvent.click(screen.getByRole("button", { name: /save/i }));

    await waitFor(() => {
      expect(updateSpy).toHaveBeenCalledWith(claim.application_id, {
        has_reduced_schedule_leave_periods: true,
        leave_details: {
          reduced_schedule_leave_periods: [
            { end_date: "2021-03-29", start_date: "2021-01-30" },
          ],
        },
      });
    });
  });
});
