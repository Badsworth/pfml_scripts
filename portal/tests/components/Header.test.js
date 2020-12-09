import Header from "../../src/components/Header";
import React from "react";
import { shallow } from "enzyme";

describe("Header", () => {
  it("includes a Skip Nav link as its first link", () => {
    const wrapper = shallow(<Header onLogout={jest.fn()} />);

    expect(wrapper).toMatchSnapshot();
    expect(wrapper.find("HeaderSlim").prop("skipNav").props.href).toBe("#main");
  });

  it("passes the user into AuthNav", () => {
    const user = {
      username: "Foo Bar",
    };

    const wrapper = shallow(<Header user={user} onLogout={jest.fn()} />);

    expect(wrapper).toMatchSnapshot();
    expect(wrapper.find("HeaderSlim").prop("utilityNav").props.user).toBe(user);
  });
});
