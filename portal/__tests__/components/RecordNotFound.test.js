import "../../src/i18n";
import React from "react";
import RecordNotFound from "../../src/components/RecordNotFound";
import { shallow } from "enzyme";

describe("RecordNotFound", () => {
  it("renders RecordNotFound component", () => {
    const wrapper = shallow(<RecordNotFound />);

    expect(wrapper).toMatchSnapshot();
  });
});
