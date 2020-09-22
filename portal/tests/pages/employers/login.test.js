import { mount, shallow } from "enzyme";
import Login from "../../../src/pages/employers/login";
import React from "react";
import { act } from "react-dom/test-utils";
import { mockRouter } from "next/router";

describe("Login", () => {
  let wrapper;

  it("renders login page", () => {
    wrapper = shallow(<Login />);
    expect(wrapper).toMatchSnapshot();
  });

  it("redirects to login page with query param", () => {
    act(() => {
      wrapper = mount(<Login />);
    });

    expect(mockRouter.push).toHaveBeenCalledWith("/login/?next=/employers");
  });
});
