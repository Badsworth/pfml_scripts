import React from "react";
import { create } from "react-test-renderer";
import Sidebar from "../../src/components/Sidebar";

jest.mock("next/router", () => require("next-router-mock"));

describe("Sidebar", () => {
  test("renders the default component", () => {
    const component = create(<Sidebar />).toJSON();
    expect(component).toMatchSnapshot();
  });

  // @todo: test environment flag at bottom of sidebar
  /*test("renders correct environment label", () => {

  });*/
});
