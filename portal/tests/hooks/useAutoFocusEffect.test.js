/* eslint-disable jsx-a11y/no-noninteractive-tabindex */
import { render, screen } from "@testing-library/react";
import AmendmentForm from "../../src/components/employers/AmendmentForm";
import ConditionalContent from "../../src/components/ConditionalContent";
import React from "react";
import useAutoFocusEffect from "../../src/hooks/useAutoFocusEffect";

describe("useAutoFocusEffect", () => {
  function TestComponent({ isAmendmentFormDisplayed }) {
    const containerRef = React.createRef();
    useAutoFocusEffect({ containerRef, isAmendmentFormDisplayed });

    return (
      <ConditionalContent visible={isAmendmentFormDisplayed}>
        <div ref={containerRef}>
          <AmendmentForm onDestroy={() => {}} destroyButtonLabel="Destroy">
            <form>
              <label htmlFor="first-name" tabIndex="0">
                First
              </label>
              <input type="text" name="first-name" id="first-name"></input>
              <label htmlFor="second-name" tabIndex="0">
                Second
              </label>
              <input type="text" name="second-name" id="second-name"></input>
            </form>
          </AmendmentForm>
        </div>
      </ConditionalContent>
    );
  }

  it("focuses the first focusable label", () => {
    render(<TestComponent isAmendmentFormDisplayed={true} />);
    expect(screen.getByText("First")).toHaveFocus();
  });
});
