import { render, screen } from "@testing-library/react";
import React from "react";
import StateDropdown from "../../src/components/StateDropdown";

describe("StateDropdown", () => {
  it("renders select field with U.S. states as options", () => {
    render(
      <StateDropdown
        label="State"
        emptyChoiceLabel="Select a state"
        name="state"
      />
    );

    expect(screen.getByRole("combobox", { name: "State" })).toMatchSnapshot();
  });
});
