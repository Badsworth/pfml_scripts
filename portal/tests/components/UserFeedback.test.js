import React from "react";
import UserFeedback from "../../src/components/UserFeedback";
import { render } from "@testing-library/react";

describe("UserFeedback", () => {
  it("renders the component", () => {
    const { container } = render(<UserFeedback url="https://example.com" />);

    expect(container.firstChild).toMatchSnapshot();
  });
});
