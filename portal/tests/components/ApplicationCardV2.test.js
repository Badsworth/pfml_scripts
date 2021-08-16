import { ApplicationCardV2 } from "../../src/components/ApplicationCardV2";
import { MockBenefitsApplicationBuilder } from "../test-utils";
import React from "react";
import { shallow } from "enzyme";

describe("ApplicationCardV2", () => {
  const render = (claim = {}) => {
    return shallow(<ApplicationCardV2 claim={claim} number={2} />);
  };

  describe("components match their snapshots", () => {
    it("status container component matches snapshot", () => {
      const wrapper = render(new MockBenefitsApplicationBuilder().create());
      expect(wrapper).toMatchSnapshot();
    });

    it("completed status component matches snapshot", () => {
      const wrapper = render(
        new MockBenefitsApplicationBuilder().completed().create()
      );
      expect(wrapper.find("StatusCard").dive()).toMatchSnapshot();
    });

    it("in progress component status matches snapshot", () => {
      const wrapper = render(new MockBenefitsApplicationBuilder().create());
      expect(wrapper.find("StatusCard").dive()).toMatchSnapshot();
    });
  });
});
