import { render, screen } from "@testing-library/react";
import React from "react";
import WeeklyTimeTable from "../../src/components/WeeklyTimeTable";

function renderComponent() {
  const days = [
    {
      day_of_week: "Sunday",
      minutes: 480,
    },
    {
      day_of_week: "Monday",
      minutes: 480,
    },
    {
      day_of_week: "Tuesday",
      minutes: 480,
    },
    {
      day_of_week: "Wednesday",
      minutes: 480,
    },
    {
      day_of_week: "Thursday",
      minutes: 480,
    },
    {
      day_of_week: "Friday",
      minutes: 480,
    },
    {
      day_of_week: "Saturday",
      minutes: 0,
    },
  ];

  return render(<WeeklyTimeTable days={days} />);
}

describe("WeeklyTimeTable", () => {
  it("renders a table with days of the week and times", () => {
    renderComponent();

    expect(screen.getByRole("table")).toMatchSnapshot();
  });

  it("only renders hours if minutes are 0", () => {
    renderComponent();

    const cells = screen.getByRole("table").querySelectorAll("td");

    expect(cells[cells.length - 1]).toHaveTextContent("0h");
  });
});
