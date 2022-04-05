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
      screen.queryByRole("button", { name: "Hide filters" })
    ).not.toBeInTheDocument();

    // Show the filters
    userEvent.click(toggleButton);

    expect(toggleButton).toHaveAccessibleName("Hide filters");
    expect(
      screen.getByRole("button", { name: "Hide filters" })
    ).toBeInTheDocument();
  });

  it("displays number of active filters in Show Filters button and filters menu", () => {
    const verifiedEmployers = [
      createMockUserLeaveAdministrator({
        employer_dba: "Acme Co",
        verified: true,
      }),
      createMockUserLeaveAdministrator({
        verified: true,
      }),
    ];

    setup({
      params: {
        is_reviewable: "yes",
        employer_id: verifiedEmployers[0].employer_id,
        request_decision: "pending",
      },
      verifiedEmployers,
    });

    expect(
      screen.getByRole("button", { name: "Show filters (3)" })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", {
        name: /Remove filter: Yes, review requested/,
      })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", {
        name: /Remove filter: Pending/,
      })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", {
        name: /Remove filter: Acme Co/,
      })
    ).toBeInTheDocument();
  });

  it("renders organizations filter when there are multiple verified organizations", () => {
    setup({
      verifiedEmployers: [
        createMockUserLeaveAdministrator({
          verified: true,
        }),
        createMockUserLeaveAdministrator({
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
      verifiedEmployers: [],
    });

    userEvent.click(screen.getByRole("button", { name: /show filters/i }));

    expect(
      screen.queryByRole("combobox", { name: /organizations/i })
    ).not.toBeInTheDocument();
  });

  it("renders leave details and is_reviewable filters", () => {
    setup();
    userEvent.click(screen.getByRole("button", { name: /show filters/i }));

    expect(
      screen.getByRole("group", { name: /leave details/i })
    ).toMatchSnapshot();

    expect(
      screen.getByRole("group", { name: /review requested/i })
    ).toMatchSnapshot();
  });
});
