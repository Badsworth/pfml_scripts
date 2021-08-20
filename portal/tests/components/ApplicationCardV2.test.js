import { ApplicationCardV2 } from "../../src/components/ApplicationCardV2";
import { MockBenefitsApplicationBuilder } from "../test-utils";
import React from "react";
import { mount } from "enzyme";

describe("ApplicationCardV2", () => {
  describe("components match their snapshots", () => {
    it("in progress component status matches snapshot", () => {
      const claim = new MockBenefitsApplicationBuilder().submitted().create();
      const wrapper = mount(<ApplicationCardV2 claim={claim} number={2} />);

      expect(wrapper).toMatchSnapshot();
    });

    it("completed status component matches snapshot", () => {
      const claim = new MockBenefitsApplicationBuilder().completed().create();
      const wrapper = mount(<ApplicationCardV2 claim={claim} />);

      expect(wrapper).toMatchSnapshot();
    });
  });
});
