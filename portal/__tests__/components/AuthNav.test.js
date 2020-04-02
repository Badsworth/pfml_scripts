import { Auth } from "aws-amplify";
import AuthNav from "../../src/components/AuthNav";
import React from "react";
import { shallow } from "enzyme";

describe("AuthNav", () => {
  describe("when a user is NOT authenticated", () => {
    it("doesn't render the logged-in state", () => {
      const wrapper = shallow(<AuthNav />);

      expect(wrapper).toMatchSnapshot();
    });

    it("doesn't render the user's name", () => {
      const wrapper = shallow(<AuthNav />);

      expect(wrapper.text()).toEqual("");
    });

    it("doesn't render a log out link", () => {
      const wrapper = shallow(<AuthNav />);

      expect(wrapper.exists("button")).toBe(false);
    });
  });

  describe("when a user is authenticated", () => {
    const user = {
      username: "Foo Bar",
    };

    it("renders the logged-in state", () => {
      const wrapper = shallow(<AuthNav user={user} />);

      expect(wrapper).toMatchSnapshot();
    });

    it("renders the user's name", () => {
      const wrapper = shallow(<AuthNav user={user} />);

      expect(wrapper.text()).toMatch(user.username);
    });

    it("renders a log out link", () => {
      const wrapper = shallow(<AuthNav user={user} />);

      expect(wrapper.find("button").text()).toEqual("Log out");
    });

    describe("when log out button is clicked", () => {
      beforeEach(() => {
        jest.spyOn(Auth, "signOut").mockImplementation(() => {});
      });

      afterEach(() => {
        jest.restoreAllMocks();
      });

      it("logs the user out", () => {
        const wrapper = shallow(<AuthNav user={user} />);
        wrapper.find("button").simulate("click");

        expect(Auth.signOut.mock.calls.length).toBe(1);
      });
    });
  });
});
