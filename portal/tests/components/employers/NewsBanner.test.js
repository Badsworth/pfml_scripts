import { NewsBanner } from "../../../src/components/employers/NewsBanner";
import React from "react";
import { shallow } from "enzyme";

describe("NewsBanner", () => {
  it("renders the component", () => {
    const wrapper = shallow(<NewsBanner />);

    expect(wrapper).toMatchSnapshot();
    expect(wrapper.find("Trans").dive()).toMatchSnapshot();
  });

  describe("when dashboard feature flag is enabled", () => {
    it("renders go live content", () => {
      process.env.featureFlags = { employerShowDashboard: true };

      const wrapper = shallow(<NewsBanner />);

      expect(wrapper).toMatchSnapshot();
      expect(wrapper.find("Trans").dive()).toMatchSnapshot();
    });
  });
});
