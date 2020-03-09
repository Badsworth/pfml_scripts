import "../../src/i18n";
import Header from "../../src/components/Header";
import React from "react";
import { shallow } from "enzyme";

describe("Header", () => {
  it("includes a Skip Nav link as its first link", () => {
    const wrapper = shallow(<Header />);
    const links = wrapper.find("a");

    expect(links.first().prop("href")).toBe("#main");
  });

  it("passes the user into AuthNav", () => {
    const user = {
      username: "Foo Bar",
    };

    const wrapper = shallow(<Header user={user} />);
    const authNav = wrapper.find("AuthNav");

    expect(authNav.prop("user")).toBe(user);
  });
});
