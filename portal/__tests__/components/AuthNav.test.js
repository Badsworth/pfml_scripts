import AuthNav from "../../components/AuthNav";
import React from "react";
import { shallow } from "enzyme";

describe("AuthNav", () => {
  describe("when a user is NOT authenticated", () => {
    it("doesn't render the logged-in state", () => {
      const wrapper = shallow(<AuthNav />);

      expect(wrapper).toMatchSnapshot();
    });
  });

  describe("when a user is authenticated", () => {
    const user = {
      name: "Foo Bar"
    };

    it("renders the logged-in state", () => {
      const wrapper = shallow(<AuthNav user={user} />);

      expect(wrapper).toMatchSnapshot();
    });

    it("renders the user's name", () => {
      const wrapper = shallow(<AuthNav user={user} />);

      expect(wrapper.text()).toMatch(user.name);
    });

    it("renders a log out link", () => {
      const wrapper = shallow(<AuthNav user={user} />);

      expect(wrapper.find("button").text()).toEqual("Log out");
    });
  });
});
