import AmendButton from "../../../src/components/employers/AmendButton";
import React from "react";
import { shallow } from "enzyme";

describe("AmendButton", () => {
  it("renders the component", () => {
    const wrapper = shallow(<AmendButton />);

    expect(wrapper).toMatchSnapshot();
  });
});
