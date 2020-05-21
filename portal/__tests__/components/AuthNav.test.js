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

      expect(wrapper.exists("Button")).toBe(false);
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

      expect(wrapper.find("Button")).toMatchInlineSnapshot(`
        <Button
          className="width-auto"
          inversed={true}
          onClick={[Function]}
          variation="unstyled"
        >
          Log out
        </Button>
      `);
    });

    describe("when log out button is clicked", () => {
      const originalLocation = window.location;

      beforeEach(() => {
        delete window.location;
        window.location = { assign: jest.fn() };

        jest.spyOn(Auth, "signOut").mockImplementation(() => {});
      });

      afterEach(() => {
        window.location = originalLocation;

        jest.restoreAllMocks();
      });

      it("logs the user out", async () => {
        const wrapper = shallow(<AuthNav user={user} />);
        await wrapper.find("Button").simulate("click");

        expect(Auth.signOut.mock.calls.length).toBe(1);
      });

      it("redirects to home page", async () => {
        const wrapper = shallow(<AuthNav user={user} />);
        await wrapper.find("Button").simulate("click");

        expect(window.location.assign).toHaveBeenCalledWith("/");
      });
    });
  });
});
