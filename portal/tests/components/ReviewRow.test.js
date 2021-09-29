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
  const dl = document.createElement("dl");
  return render(<ReviewRow {...props} />, {
    container: document.body.appendChild(dl),
  });
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

  it("associates definitions with the appropriate terms", () => {
    renderRow();
    const definition = screen.getByRole("definition", { name: "Leave type" });
    expect(definition).toHaveTextContent("Medical");
  });
});
