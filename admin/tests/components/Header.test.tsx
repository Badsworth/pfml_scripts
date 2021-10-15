import React from "react";
import { create } from "react-test-renderer";
import Header from "../../src/components/Header";

describe("Header", () => {
  test("renders the default component", () => {
    const component = create(<Header />).toJSON();
    expect(component).toMatchSnapshot();
  });
});
