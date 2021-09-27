import { render, screen } from "@testing-library/react";
import React from "react";
import ReviewHeading from "../../src/components/ReviewHeading";

const renderComponent = (customProps) => {
  const props = {
    children: "Who is taking leave?",
    level: "2",
    ...customProps,
  };
  return render(<ReviewHeading {...props} />);
};

describe("ReviewHeading", () => {
  it("renders a Heading, no link if editHref not defined", () => {
    const { container } = renderComponent();
    expect(container.firstChild).toMatchSnapshot();
    expect(screen.queryByRole("link")).not.toBeInTheDocument();
  });

  it("when editHref is defined renders with an edit link", () => {
    const { container } = renderComponent({
      editHref: "/name",
      editText: "Edit",
    });
    expect(container.firstChild).toMatchSnapshot();
    expect(screen.queryByRole("link")).toBeInTheDocument();
  });
});
