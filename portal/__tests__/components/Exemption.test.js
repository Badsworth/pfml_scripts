import "../../src/i18n";
import Exemption from "../../src/components/Exemption";
import React from "react";
import { shallow } from "enzyme";

describe("Exemption", () => {
  it("renders Exemption component", () => {
    const wrapper = shallow(<Exemption />);

    expect(wrapper).toMatchSnapshot();
  });
});
