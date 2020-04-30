import BackButton from "../../src/components/BackButton";
import React from "react";
import { shallow } from "enzyme";

describe("<BackButton>", () => {
  it("renders the back button", () => {
    const wrapper = shallow(<BackButton />);

    expect(wrapper.name()).toBe("Button");
    expect(wrapper.dive().text()).toBe("Back");
  });

  describe("when clicked", () => {
    it("routes to previous page", () => {
      const spy = jest.spyOn(window.history, "back");

      const wrapper = shallow(<BackButton />);

      wrapper.simulate("click");

      expect(spy).toHaveBeenCalledTimes(1);
    });
  });
});
