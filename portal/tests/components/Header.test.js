import User, { RoleDescription, UserRole } from "../../src/models/User";
import Header from "../../src/components/Header";
import React from "react";
import { shallow } from "enzyme";

describe("Header", () => {
  it("includes a Skip Nav link as its first link", () => {
    const wrapper = shallow(<Header onLogout={jest.fn()} />);

    expect(wrapper).toMatchSnapshot();
    expect(wrapper.find(".usa-skipnav").props().href).toBe("#main");
  });

  it("renders Header for logged in claimant", () => {
    const user = new User({
      email_address: "email@address.com",
      user_id: "mock-user-id",
    });

    const wrapper = shallow(<Header user={user} onLogout={jest.fn()} />);

    expect(wrapper).toMatchSnapshot();
    expect(wrapper.find("HeaderSlim").prop("utilityNav").props.user).toBe(user);
  });

  it("doesn't render beta banner when user isn't logged in", () => {
    const wrapper = shallow(<Header onLogout={jest.fn()} />);

    expect(wrapper.find("BetaBanner").exists()).toBe(false);
  });

  it("renders beta banner with employer feedback link when user is an employer", () => {
    const user = new User({
      email_address: "email@address.com",
      user_id: "mock-user-id",
      roles: [
        new UserRole({
          role_description: RoleDescription.employer,
        }),
      ],
    });
    const wrapper = shallow(<Header user={user} onLogout={jest.fn()} />);

    expect(
      wrapper.find("BetaBanner").prop("feedbackUrl")
    ).toMatchInlineSnapshot(
      `"https://www.mass.gov/paidleave-employer-feedback"`
    );
  });
});
