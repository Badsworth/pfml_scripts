import BetaBanner from "../../src/components/BetaBanner";
import React from "react";
import { render } from "@testing-library/react";

describe("BetaBanner", () => {
  it("renders message with given feedbackUrl", () => {
    const { container } = render(
      <BetaBanner feedbackUrl="http://example.com" />
    );

    expect(container.firstChild).toMatchSnapshot();
  });
});
