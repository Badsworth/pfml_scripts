import { render, screen } from "@testing-library/react";
import Filters from "../../../src/features/employer-dashboard/Filters";
import React from "react";
import createMockUserLeaveAdministrator from "../../../lib/mock-helpers/createMockUserLeaveAdministrator";
import userEvent from "@testing-library/user-event";

const setup = (props = {}) => {
  const updatePageQuerySpy = jest.fn();
  const utils = render(
    <Filters
      updatePageQuery={updatePageQuerySpy}
      params={{}}
      verifiedEmployers={[]}
      {...props}
    />
  );
  return { ...utils, updatePageQuerySpy };
};

describe("Filters", () => {
  it("toggles filters visibility when Show Filters button is clicked", () => {
    setup();
    const toggleButton = screen.getByRole("button", { name: "Show filters" });

    // Collapsed by default
    expect(
      screen.queryByRole("group", { name: /status/i })
    ).not.toBeInTheDocument();

    // Show the filters
    userEvent.click(toggleButton);

    expect(toggleButton).toHaveAccessibleName("Hide filters");
    expect(
      screen.queryByRole("group", { name: /status/i })
    ).toBeInTheDocument();
  });

  it("renders organizations filter when there are multiple verified organizations", () => {
    setup({
      verifiedEmployers: [
        createMockUserLeaveAdministrator({
          employer_dba: "Work Inc",
          employer_id: "mock-id-1",
          employer_fein: "11-3456789",
          verified: true,
        }),
        createMockUserLeaveAdministrator({
          employer_dba: "Acme",
          employer_id: "mock-id-2",
          employer_fein: "22-3456789",
          verified: true,
        }),
      ],
    });

    userEvent.click(screen.getByRole("button", { name: /show filters/i }));

    expect(
      screen.getByRole("combobox", { name: /organizations/i })
    ).toBeInTheDocument();
  });

  it("does not render organizations filter when there is only one verified organizations", () => {
    setup({
      verifiedEmployers: [
        createMockUserLeaveAdministrator({
          employer_dba: "Work Inc",
          employer_id: "mock-id-1",
          employer_fein: "11-3456789",
          verified: true,
        }),
      ],
    });

    userEvent.click(screen.getByRole("button", { name: /show filters/i }));

    expect(
      screen.queryByRole("combobox", { name: /organizations/i })
    ).not.toBeInTheDocument();
  });

  it("does not render organizations filter when there is no verified organizations", () => {
    setup({
      verifiedEmployers: [
        createMockUserLeaveAdministrator({
          employer_dba: "Work Inc",
          employer_id: "mock-id-1",
          employer_fein: "11-3456789",
          verified: false,
        }),
      ],
    });

    userEvent.click(screen.getByRole("button", { name: /show filters/i }));

    expect(
      screen.queryByRole("combobox", { name: /organizations/i })
    ).not.toBeInTheDocument();
  });
});
