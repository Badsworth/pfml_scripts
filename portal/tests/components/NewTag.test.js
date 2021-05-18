import NewTag from "../../src/components/NewTag";
import React from "react";
import { shallow } from "enzyme";

describe("NewTag", () => {
  it("renders the component", () => {
    const wrapper = shallow(<NewTag />);

    expect(wrapper).toMatchSnapshot();
  });
});
