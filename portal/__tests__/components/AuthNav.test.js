import AuthNav from "../../components/AuthNav";
import React from "react";
import { shallow } from "enzyme";

describe("AuthNav", () => {
  describe("when a user is NOT authenticated", () => {
    it("renders the logged-out state", () => {
      const wrapper = shallow(<AuthNav />);

      expect(wrapper).toMatchSnapshot();
    });

    it.todo("renders a log in link");
  });

  describe("when a user is authenticated", () => {
    it("renders the logged-in state", () => {
      const user = {
        name: "Foo Bar"
      };

      const wrapper = shallow(<AuthNav user={user} />);

      expect(wrapper).toMatchSnapshot();
    });

    it("renders the user's name", () => {
      const user = {
        name: "Foo Bar"
      };

      const wrapper = shallow(<AuthNav user={user} />);

      expect(wrapper.text()).toMatch(user.name);
    });

    it.todo("renders a log out link");
  });
});
