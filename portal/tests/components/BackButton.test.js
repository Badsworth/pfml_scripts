import BackButton from "../../src/components/BackButton";
import React from "react";
import { shallow } from "enzyme";
import tracker from "../../src/services/tracker";

function mockHistoryApi(length) {
  class MockHistory {
    get length() {
      return length;
    }
  }

  return new MockHistory();
}

describe("<BackButton>", () => {
  beforeEach(() => {
    // Simulate browser history so the button thinks there's a page to go back to
    history.pushState({}, "Mock page");
    history.pushState({}, "Mock page");
  });

  it("renders the back button", () => {
    const wrapper = shallow(<BackButton />);

    expect(wrapper.name()).toBe("Button");
    expect(wrapper.dive().text()).toBe("Back");
  });

  it("does not render the back button when there's no page to go back to", () => {
    const mockHistory = mockHistoryApi(1);

    const wrapper = shallow(<BackButton history={mockHistory} />);
    expect(wrapper.isEmptyRender()).toBe(true);
  });

  describe("when clicked", () => {
    it("routes to previous page", () => {
      const spy = jest.spyOn(window.history, "back");

      const wrapper = shallow(<BackButton />);

      wrapper.simulate("click");

      expect(spy).toHaveBeenCalledTimes(1);
    });

    it("tracks event", () => {
      const spy = jest.spyOn(tracker, "trackEvent");

      const wrapper = shallow(<BackButton />);

      wrapper.simulate("click");

      expect(spy).toHaveBeenCalledWith("BackButton clicked");
    });
  });

  describe("when label prop is defined", () => {
    it("sets back button label", () => {
      const label = "Back to checklist";
      const wrapper = shallow(<BackButton label={label} />);

      expect(wrapper.dive().text()).toEqual(label);
    });
  });

  describe("when href prop is defined", () => {
    it("renders button link", () => {
      const wrapper = shallow(<BackButton href="/prev" />);

      expect(wrapper.name()).toBe("ButtonLink");
      const link = wrapper.dive().dive();
      expect(link.text()).toBe("Back");
      expect(link.prop("href")).toEqual("/prev");
    });

    it("tracks event when clicked", () => {
      const spy = jest.spyOn(tracker, "trackEvent");

      const wrapper = shallow(<BackButton href="/prev" />);

      wrapper.simulate("click");

      expect(spy).toHaveBeenCalledWith("BackButton clicked");
    });
  });
});
