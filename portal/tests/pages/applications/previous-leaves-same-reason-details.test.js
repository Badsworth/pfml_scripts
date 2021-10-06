import { MockBenefitsApplicationBuilder, renderPage } from "../../test-utils";
import { cleanup, screen, waitFor, within } from "@testing-library/react";
import PreviousLeavesSameReasonDetails from "../../../src/pages/applications/previous-leaves-same-reason-details";
import { setupBenefitsApplications } from "../../test-utils/helpers";
import userEvent from "@testing-library/user-event";

const setup = (
  claim = new MockBenefitsApplicationBuilder()
    .bondingLeaveReason()
    .employed()
    .continuous()
    .create()
) => {
  let updateSpy;

  const utils = renderPage(
    PreviousLeavesSameReasonDetails,
    {
      addCustomSetup: (appLogic) => {
        setupBenefitsApplications(appLogic, [claim]);
        updateSpy = jest.spyOn(appLogic.benefitsApplications, "update");
      },
    },
    { query: { claim_id: claim.application_id } }
  );

  return {
    updateSpy,
    ...utils,
  };
};

const clickAddPreviousLeaveButton = () => {
  userEvent.click(screen.getByRole("button", { name: /Add/i }));
};

describe("PreviousLeavesSameReasonDetails", () => {
  it("renders the page", () => {
    const { container } = setup();
    expect(container).toMatchSnapshot();
  });

  it("adds an empty previous leave when the user clicks Add Previous Leave", () => {
    setup();

    expect(
      screen.getByRole("group", { name: /previous leave/i })
    ).toBeInTheDocument();

    clickAddPreviousLeaveButton();

    expect(
      screen.getAllByRole("group", { name: /previous leave/i })
    ).toHaveLength(2);
  });

  it("removes a previous leave when user clicks Remove Leave", () => {
    setup();

    clickAddPreviousLeaveButton();

    expect(
      screen.getAllByRole("group", { name: /previous leave/i })
    ).toHaveLength(2);

    userEvent.click(screen.getAllByRole("button", { name: /Remove/i })[0]);

    expect(
      screen.getByRole("group", { name: /previous leave/i })
    ).toBeInTheDocument();
  });

  it("changes date in hint text when claim is for caring leave", () => {
    const julyTextMatch = /leave taken between July 1, 2021/i;
    const januaryTextMatch = /leave taken between January 1, 2021/i;

    setup(
      new MockBenefitsApplicationBuilder()
        .continuous()
        .employed()
        .previousLeavesSameReason()
        .caringLeaveReason()
        .create()
    );

    expect(screen.queryByText(julyTextMatch)).toBeInTheDocument();
    expect(screen.queryByText(januaryTextMatch)).not.toBeInTheDocument();

    cleanup();
    setup(
      new MockBenefitsApplicationBuilder()
        .continuous()
        .employed()
        .previousLeavesSameReason()
        .medicalLeaveReason()
        .create()
    );

    expect(screen.queryByText(julyTextMatch)).not.toBeInTheDocument();
    expect(screen.queryByText(januaryTextMatch)).toBeInTheDocument();
  });

  it("calls update when user submits form with new data", async () => {
    const { updateSpy } = setup();

    userEvent.click(
      screen.getByRole("radio", {
        name: "Yes",
      })
    );
    const [startMonthInput, endMonthInput] = screen.getAllByRole("textbox", {
      name: "Month",
    });
    const [startDayInput, endDayInput] = screen.getAllByRole("textbox", {
      name: "Day",
    });
    const [startYearInput, endYearInput] = screen.getAllByRole("textbox", {
      name: "Year",
    });

    userEvent.type(startDayInput, "1");
    userEvent.type(startMonthInput, "3");
    userEvent.type(startYearInput, "2021");
    userEvent.type(endDayInput, "2");
    userEvent.type(endMonthInput, "4");
    userEvent.type(endYearInput, "2021");

    userEvent.type(
      within(
        screen.getByRole("group", {
          name: /hours would you normally have worked per week/i,
        })
      ).getByRole("textbox", { name: /Hours/i }),
      "40"
    );
    userEvent.type(
      within(
        screen.getByRole("group", {
          name: /total number of hours you took off/i,
        })
      ).getByRole("textbox", { name: /Hours/i }),
      "14"
    );

    userEvent.click(screen.getByRole("button", { name: /save/i }));

    await waitFor(() => {
      expect(updateSpy).toHaveBeenCalledWith(expect.any(String), {
        previous_leaves_same_reason: [
          {
            is_for_current_employer: true,
            leave_end_date: "2021-04-02",
            leave_minutes: 840,
            leave_reason: null,
            leave_start_date: "2021-03-01",
            previous_leave_id: null,
            type: null,
            worked_per_week_minutes: 2400,
          },
        ],
      });
    });
  });

  it("calls update when user submits form with existing data", async () => {
    const claim = new MockBenefitsApplicationBuilder()
      .employed()
      .previousLeavesSameReason()
      .create();
    const previousLeave = claim.previous_leaves_same_reason[0];
    const { updateSpy } = setup(claim);

    userEvent.click(screen.getByRole("button", { name: /save/i }));

    await waitFor(() => {
      expect(updateSpy).toHaveBeenCalledWith(claim.application_id, {
        previous_leaves_same_reason: [previousLeave],
      });
    });
  });
});
