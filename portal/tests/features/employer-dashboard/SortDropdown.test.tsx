import { render, screen } from "@testing-library/react";
import React from "react";
import SortDropdown from "../../../src/features/employer-dashboard/SortDropdown";
import userEvent from "@testing-library/user-event";

const setup = () => {
  const updatePageQuerySpy = jest.fn();
  const utils = render(<SortDropdown updatePageQuery={updatePageQuerySpy} />);
  return { ...utils, updatePageQuerySpy };
};

describe("SortDropdown", () => {
  it("defaults to Sort by Status option", () => {
    setup();

    expect(screen.getByRole("combobox", { name: /sort/i })).toHaveValue(
      "absence_status,ascending"
    );
  });

  it("defaults to Sort by New applications option when is enabled", () => {
    process.env.featureFlags = JSON.stringify({
      employerShowMultiLeaveDashboard: true,
    });
    setup();

    expect(screen.getByRole("combobox", { name: /sort/i })).toHaveValue(
      "latest_follow_up_date,descending"
    );
  });

  it("updates order_by and order_direction params when a sort choice is selected", () => {
    const { updatePageQuerySpy } = setup();

    userEvent.selectOptions(screen.getByRole("combobox"), [
      "employee,ascending",
    ]);

    expect(updatePageQuerySpy).toHaveBeenCalledWith([
      { name: "order_by", value: "employee" },
      { name: "order_direction", value: "ascending" },
      { name: "page_offset", value: "1" },
    ]);
  });
});
