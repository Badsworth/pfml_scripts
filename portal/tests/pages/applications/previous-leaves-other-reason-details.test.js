import { MockBenefitsApplicationBuilder, renderPage } from "../../test-utils";
import { cleanup, screen, waitFor, within } from "@testing-library/react";
import PreviousLeavesOtherReasonDetails from "../../../src/pages/applications/previous-leaves-other-reason-details";
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
    PreviousLeavesOtherReasonDetails,
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

describe("PreviousLeavesOtherReasonDetails", () => {
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

  it("changes hint date if claim is caring leave or starts in 2021", () => {
    const januaryTextMatch = /leave taken between January 1, 2021/i;
    const marchTextMatch = /leave taken between March 7, 2021/i;
    const julyTextMatch = /leave taken between July 1, 2021/i;

    setup(
      new MockBenefitsApplicationBuilder()
        .continuous({
          start_date: "2021-11-01",
        })
        .employed()
        .previousLeavesSameReason()
        .medicalLeaveReason()
        .create()
    );

    expect(screen.queryByText(januaryTextMatch)).toBeInTheDocument();
    expect(screen.queryByText(marchTextMatch)).not.toBeInTheDocument();
    expect(screen.queryByText(julyTextMatch)).not.toBeInTheDocument();

    cleanup();
    setup(
      new MockBenefitsApplicationBuilder()
        .continuous({
          start_date: "2022-03-07",
        })
        .employed()
        .previousLeavesSameReason()
        .caringLeaveReason()
        .create()
    );

    expect(screen.queryByText(januaryTextMatch)).not.toBeInTheDocument();
    expect(screen.queryByText(marchTextMatch)).not.toBeInTheDocument();
    expect(screen.queryByText(julyTextMatch)).toBeInTheDocument();

    cleanup();
    setup(
      new MockBenefitsApplicationBuilder()
        .continuous({
          start_date: "2022-03-07",
        })
        .employed()
        .previousLeavesSameReason()
        .medicalLeaveReason()
        .create()
    );

    expect(screen.queryByText(januaryTextMatch)).not.toBeInTheDocument();
    expect(screen.queryByText(marchTextMatch)).toBeInTheDocument();
    expect(screen.queryByText(julyTextMatch)).not.toBeInTheDocument();
  });

  it("calls update when user submits form with new data", async () => {
    const { updateSpy } = setup();

    userEvent.click(
      screen.getByRole("radio", {
        name: "An illness or injury",
      })
    );
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
    userEvent.type(startYearInput, "2022");
    userEvent.type(endDayInput, "2");
    userEvent.type(endMonthInput, "4");
    userEvent.type(endYearInput, "2022");

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
        previous_leaves_other_reason: [
          {
            is_for_current_employer: true,
            leave_end_date: "2022-04-02",
            leave_minutes: 840,
            leave_reason: "An illness or injury",
            leave_start_date: "2022-03-01",
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
      .previousLeavesOtherReason()
      .create();
    const previousLeave = claim.previous_leaves_other_reason[0];
    const { updateSpy } = setup(claim);

    userEvent.click(screen.getByRole("button", { name: /save/i }));

    await waitFor(() => {
      expect(updateSpy).toHaveBeenCalledWith(claim.application_id, {
        previous_leaves_other_reason: [previousLeave],
      });
    });
  });
});
