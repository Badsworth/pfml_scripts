/* eslint-disable import/first */
jest.mock("react", () => ({
  ...jest.requireActual("react"),
  // Mock useEffect so that we can manipulate it below
  useEffect: jest.fn(),
}));

import React, { useEffect } from "react";
import { mount, shallow } from "enzyme";
import Login from "../../../src/pages/employers/login";
import { act } from "react-dom/test-utils";
import { mockRouter } from "next/router";

describe("Login", () => {
  let wrapper;

  it("renders login page", () => {
    wrapper = shallow(<Login />);
    expect(wrapper).toMatchSnapshot();
  });

  it("redirects to login page with query param", () => {
    useEffect.mockImplementationOnce((f) => f());

    act(() => {
      wrapper = mount(<Login />);
    });

    expect(mockRouter.push).toHaveBeenCalledWith("/login/?next=/employers");
  });
});
