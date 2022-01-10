import React from "react";
import { create } from "react-test-renderer";
import Sidebar from "../../src/components/Sidebar";
import { AdminUserResponse } from "../../src/api";

jest.mock("next/router", () => require("next-router-mock"));

const mockUser: AdminUserResponse = {
  sub_id: "mock_user",
  email_address: "mock@user.com",
  groups: ["NON_PROD", "NON_PROD_ADMIN"],
  permissions: ["USER_READ"],
};

describe("Sidebar", () => {
  test("renders the default component", () => {
    const component = create(<Sidebar user={mockUser} />).toJSON();
    expect(component).toMatchSnapshot();
  });

  // @todo: test environment flag at bottom of sidebar
  /*test("renders correct environment label", () => {

  });*/
});
