import "../../src/i18n";
import React from "react";
import Result from "../../src/pages/eligibility/result";
import { shallow } from "enzyme";

describe("Result", () => {
  describe("when the employer has an exemption", () => {
    it("renders the exemption information", () => {
      const wrapper = shallow(<Result />);

      expect(wrapper).toMatchSnapshot();
    });
  });
});
