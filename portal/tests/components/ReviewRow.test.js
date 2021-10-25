import { render, screen } from "@testing-library/react";
import React from "react";
import ReviewRow from "../../src/components/ReviewRow";

const renderRow = (customProps) => {
  const props = {
    children: "Medical",
    label: "Leave type",
    level: "3",
    ...customProps,
  };
  return render(<ReviewRow {...props} />);
};

describe("ReviewRow", () => {
  it("accepts a string as children", () => {
    renderRow();
    expect(screen.getByText(/Medical/)).toBeInTheDocument();
  });

  it("accepts html as a child", () => {
    renderRow({ children: <p className="test-html">Hello World</p> });
    expect(screen.getByText(/Hello World/)).toHaveClass("test-html");
    expect(document.querySelector(".border-bottom-2px")).toBeInTheDocument();
  });

  it("excludes border classes when noBorder is set", () => {
    renderRow({ noBorder: true });
    expect(
      document.querySelector(".border-bottom-2px")
    ).not.toBeInTheDocument();
  });

  it("when editHref is defined it renders an edit link", () => {
    renderRow({
      editHref: "/name",
      editText: "Edit name",
    });
    expect(
      screen.getByRole("link", { name: "Edit name: Leave type" })
    ).toBeInTheDocument();
  });

  it("without editHref there is no edit link rendered", () => {
    renderRow();
    expect(screen.queryByRole("link")).not.toBeInTheDocument();
  });
});
