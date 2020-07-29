import Fieldset from "../../src/components/Fieldset";
import React from "react";
import { shallow } from "enzyme";

describe("Fieldset", () => {
  it("renders Fieldset component with children", () => {
    const wrapper = shallow(<Fieldset>child</Fieldset>);

    expect(wrapper).toMatchSnapshot();
  });

  describe("when className prop is set", () => {
    it("appends classname to fieldset classnames", () => {
      const wrapper = shallow(<Fieldset className="a-class" />);

      expect(wrapper.find("fieldset").prop("className")).toEqual(
        "usa-fieldset a-class"
      );
    });
  });
});
