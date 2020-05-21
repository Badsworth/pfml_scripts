import React from "react";
import Success from "../../../src/pages/claims/success";
import { shallow } from "enzyme";

describe("Success", () => {
  it("renders Success page", () => {
    const wrapper = shallow(<Success />);

    expect(wrapper).toMatchSnapshot();
  });
});
