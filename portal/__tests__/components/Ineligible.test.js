import "../../src/i18n";
import Ineligible from "../../src/components/Ineligible";
import React from "react";
import { shallow } from "enzyme";

describe("Ineligible", () => {
  it("renders Ineligible component", () => {
    const wrapper = shallow(<Ineligible employeeId="1234" />);

    expect(wrapper).toMatchSnapshot();
  });
});
