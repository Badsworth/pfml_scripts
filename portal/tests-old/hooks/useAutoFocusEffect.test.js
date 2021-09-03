import AmendmentForm from "../../src/components/employers/AmendmentForm";
import ConditionalContent from "../../src/components/ConditionalContent";
import React from "react";
import { act } from "react-dom/test-utils";
import { mount } from "enzyme";
import useAutoFocusEffect from "../../src/hooks/useAutoFocusEffect";

describe("useAutoFocusEffect", () => {
  // eslint-disable-next-line react/prop-types
  function TestComponent({ isAmendmentFormDisplayed }) {
    const containerRef = React.createRef();
    useAutoFocusEffect({ containerRef, isAmendmentFormDisplayed });

    return (
      <ConditionalContent visible={isAmendmentFormDisplayed}>
        <div ref={containerRef}>
          <AmendmentForm onDestroy={() => {}} destroyButtonLabel="Destroy">
            <form>
              {/* eslint-disable-next-line jsx-a11y/no-noninteractive-tabindex */}
              <label htmlFor="first-name" tabIndex="0">
                First
              </label>
              <input type="text" name="first-name"></input>
              {/* eslint-disable-next-line jsx-a11y/no-noninteractive-tabindex */}
              <label htmlFor="second-name" tabIndex="0">
                Second
              </label>
              <input type="text" name="second-name"></input>
            </form>
          </AmendmentForm>
        </div>
      </ConditionalContent>
    );
  }

  it("changes the focused element when the form is displayed", () => {
    // Hide warning about rendering in the body, since we need to for this test
    jest.spyOn(console, "error").mockImplementationOnce(jest.fn());
    const wrapper = mount(<TestComponent isAmendmentFormDisplayed={false} />, {
      // attachTo the body so document.activeElement works (https://github.com/enzymejs/enzyme/issues/2337#issuecomment-608984530)
      attachTo: document.body,
    });

    act(() => {
      wrapper.setProps({ isAmendmentFormDisplayed: true });
    });
    wrapper.update();

    const label = wrapper.find('label[htmlFor="first-name"]').getDOMNode();
    expect(document.activeElement).toBe(label);
  });
});
