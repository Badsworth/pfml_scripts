import React from "react";
import Spinner from "../../src/components/Spinner";
import { shallow } from "enzyme";

describe("Spinner", () => {
  it("renders spinner with the given aria text", () => {
    const text = "Loading!";

    const wrapper = shallow(<Spinner aria-valuetext={text} />);

    expect(wrapper).toMatchInlineSnapshot(`
      <span
        aria-valuetext="Loading!"
        className="c-spinner"
        role="progressbar"
      />
    `);
  });
});
