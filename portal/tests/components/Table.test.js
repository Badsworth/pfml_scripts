import React from "react";
import Table from "../../src/components/Table";
import { shallow } from "enzyme";

describe("Table", () => {
  it("renders a component with default classes", () => {
    const wrapper = shallow(<Table />);

    expect(wrapper.prop("className")).toBe(
      "usa-table usa-table--borderless c-table"
    );
  });

  it("renders a component with class name", () => {
    const wrapper = shallow(<Table className="some-style additional-style" />);

    expect(wrapper.prop("className")).toBe(
      "usa-table usa-table--borderless c-table some-style additional-style"
    );
  });

  it("renders children", () => {
    const text = "This is a caption for a table";
    const wrapper = shallow(
      <Table>
        <caption>{text}</caption>
      </Table>
    );

    expect(wrapper.children()).toHaveLength(1);
    expect(wrapper.find("caption").text()).toMatch(text);
  });
});
