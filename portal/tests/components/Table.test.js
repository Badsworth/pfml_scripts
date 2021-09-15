import { render, screen } from "@testing-library/react";
import React from "react";
import Table from "../../src/components/Table";

describe("Table", () => {
  it("renders children within a table", () => {
    render(
      <Table>
        <caption>Test table</caption>
        <thead>
          <tr>
            <th>Header 1</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td>Cell 1</td>
          </tr>
        </tbody>
      </Table>
    );

    expect(screen.getByRole("table", { name: "Test table" })).toMatchSnapshot();
  });

  it("supports additional class names", () => {
    render(<Table className="some-style additional-style" />);

    expect(screen.getByRole("table")).toHaveClass(
      "usa-table usa-table--borderless c-table some-style additional-style"
    );
  });

  it("adds a stacked modifier class when the responsive prop is set", () => {
    render(<Table responsive />);

    expect(screen.getByRole("table")).toHaveClass("usa-table--stacked-header");
  });

  it("nests the table in a scrollable container when the scrollable prop is set", () => {
    const { container } = render(<Table scrollable />);

    expect(container.firstChild).toHaveClass("usa-table-container--scrollable");
    expect(container.firstChild.firstChild).toBe(screen.getByRole("table"));
  });
});
