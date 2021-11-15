import React from "react";
import StepNumber from "../../src/components/StepNumber";
import { render } from "@testing-library/react";

describe("StepNumber", () => {
  it("renders the component", () => {
    const { container } = render(
      <StepNumber screenReaderPrefix="Step" state="disabled">
        1
      </StepNumber>
    );

    expect(container.firstChild).toMatchInlineSnapshot(`
<div
  aria-label="Step 1"
  class="radius-pill text-center height-5 width-5 margin-top-2px font-sans-md border-2px line-height-sans-5 border-base text-base"
>
  1
</div>
`);
  });

  it("renders an outlined number when state is disabled", () => {
    const { container } = render(
      <StepNumber screenReaderPrefix="Step" state="disabled">
        1
      </StepNumber>
    );

    expect(container.firstChild).toHaveClass("border-2px");
  });

  it("renders an black filled number when state is completed", () => {
    const { container } = render(
      <StepNumber screenReaderPrefix="Step" state="completed">
        1
      </StepNumber>
    );

    expect(container.firstChild).toHaveClass("bg-black");
  });

  it("renders an secondary filled number when state is in_progress or not_started", () => {
    const { container: inProgress } = render(
      <StepNumber screenReaderPrefix="Step" state="in_progress">
        1
      </StepNumber>
    );

    const { container: notStarted } = render(
      <StepNumber screenReaderPrefix="Step" state="not_started">
        1
      </StepNumber>
    );

    expect(inProgress.firstChild).toHaveClass("bg-secondary");
    expect(notStarted.firstChild).toHaveClass("bg-secondary");
  });
});
