import { AbsencePeriodRequestDecision } from "../../../src/models/AbsencePeriod";
import AbsencePeriodStatusTag from "../../../src/components/AbsencePeriodStatusTag";
import React from "react";
import { render } from "@testing-library/react";

describe("AbsencePeriodStatusTag", () => {
  it.each(Object.values(AbsencePeriodRequestDecision))(
    "renders tag for %s",
    (decision) => {
      const { container } = render(
        <AbsencePeriodStatusTag request_decision={decision} />
      );
      expect(container.firstChild).toMatchSnapshot();
    }
  );

  it("returns null when the decision is undefined", () => {
    const { container } = render(<AbsencePeriodStatusTag />);

    expect(container).toBeEmptyDOMElement();
  });
});
