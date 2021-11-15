import { MockBenefitsApplicationBuilder, renderPage } from "../../test-utils";
import { screen, waitFor } from "@testing-library/react";
import ConcurrentLeavesDetails from "../../../src/pages/applications/concurrent-leaves-details";
import { setupBenefitsApplications } from "../../test-utils/helpers";
import userEvent from "@testing-library/user-event";

const updateClaim = jest.fn(() => {
  return Promise.resolve();
});

const setup = () => {
  const claims = [
    new MockBenefitsApplicationBuilder().employed().continuous().create(),
  ];
  const cb = (appLogic) => {
    appLogic.benefitsApplications.update = updateClaim;
  };
  return renderPage(
    ConcurrentLeavesDetails,
    {
      addCustomSetup: (hook) => {
        setupBenefitsApplications(hook, claims, cb);
      },
    },
    { query: { claim_id: "mock_application_id" } }
  );
};

const concurrentLeaveData = {
  is_for_current_employer: true,
  leave_start_date: "2021-05-01",
  leave_end_date: "2021-06-01",
};

describe("ConcurrentLeavesDetails", () => {
  it("renders the page", () => {
    const { container } = setup();
    expect(container).toMatchSnapshot();
  });

  it("calls claims.update with new concurrent leave data when user clicks continue", async () => {
    setup();
    userEvent.click(screen.getByRole("radio", { name: "Yes" }));
    const [startMonth, endMonth] = screen.getAllByRole("textbox", {
      name: "Month",
    });
    const [startDay, endDay] = screen.getAllByRole("textbox", { name: "Day" });
    const [startYear, endYear] = screen.getAllByRole("textbox", {
      name: "Year",
    });

    userEvent.type(startMonth, "5");
    userEvent.type(startDay, "1");
    userEvent.type(startYear, "2021");
    userEvent.type(endMonth, "6");
    userEvent.type(endDay, "1");
    userEvent.type(endYear, "2021");

    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));

    await waitFor(() => {
      expect(updateClaim).toHaveBeenCalledWith("mock_application_id", {
        concurrent_leave: concurrentLeaveData,
      });
    });
  });

  it("calls claims.update with empty concurrent leave data when user does not enter data", async () => {
    setup();

    userEvent.click(screen.getByRole("button", { name: "Save and continue" }));
    await waitFor(() => {
      expect(updateClaim).toHaveBeenCalledWith("mock_application_id", {
        concurrent_leave: {
          is_for_current_employer: null,
          leave_start_date: null,
          leave_end_date: null,
        },
      });
    });
  });
});
