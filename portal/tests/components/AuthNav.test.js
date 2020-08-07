import AuthNav from "../../src/components/AuthNav";
import React from "react";
import User from "../../src/models/User";
import { shallow } from "enzyme";

describe("AuthNav", () => {
  describe("when a user is NOT authenticated", () => {
    it("doesn't render the logged-in state", () => {
      const wrapper = shallow(<AuthNav onLogout={jest.fn()} />);

      expect(wrapper).toMatchSnapshot();
    });

    it("doesn't render the user's name", () => {
      const wrapper = shallow(<AuthNav onLogout={jest.fn()} />);

      expect(wrapper.text()).toEqual("");
    });

    it("doesn't render a log out link", () => {
      const wrapper = shallow(<AuthNav onLogout={jest.fn()} />);

      expect(wrapper.exists("Button")).toBe(false);
    });
  });

  describe("when a user is authenticated", () => {
    const user = new User({
      email_address: "email@address.com",
      user_id: "mock-user-id",
    });

    it("renders the logged-in state", () => {
      const wrapper = shallow(
        <AuthNav user={user} onLogout={() => jest.fn()} />
      );

      expect(wrapper).toMatchSnapshot();
    });

    it("renders the user's name", () => {
      const wrapper = shallow(<AuthNav user={user} onLogout={jest.fn()} />);

      expect(wrapper.text()).toMatch(user.email_address);
    });

    it("renders a log out link", () => {
      const wrapper = shallow(
        <AuthNav user={user} onLogout={() => jest.fn()} />
      );

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
      it("logs the user out", async () => {
        const signOut = jest.fn();
        const wrapper = shallow(<AuthNav user={user} onLogout={signOut} />);
        await wrapper.find("Button").simulate("click");

        expect(signOut.mock.calls.length).toBe(1);
      });
    });
  });
});
