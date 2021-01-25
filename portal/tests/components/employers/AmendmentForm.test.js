import AmendmentForm from "../../../src/components/employers/AmendmentForm";
import React from "react";
import { shallow } from "enzyme";

describe("AmendmentForm", () => {
  it("renders the component", () => {
    const wrapper = shallow(
      <AmendmentForm>
        <p>Testing</p>
      </AmendmentForm>
    );

    expect(wrapper).toMatchSnapshot();
  });
});
