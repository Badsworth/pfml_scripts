import React from "react";
import StatusRow from "../../src/components/StatusRow";
import { shallow } from "enzyme";

describe("StatusRow", () => {
  const element = <p>Testing</p>;
  const label = "Test label";
  let wrapper;

  it("renders the component", () => {
    wrapper = shallow(<StatusRow label={label}>{element}</StatusRow>);
    expect(wrapper).toMatchSnapshot();
    expect(wrapper.prop("className")).toEqual(
      "margin-bottom-2 padding-bottom-2"
    );
  });

  it("renders the component with additional class name", () => {
    wrapper = shallow(
      <StatusRow label={label} className="test-class">
        {element}
      </StatusRow>
    );
    expect(wrapper.prop("className")).toEqual(
      "margin-bottom-2 padding-bottom-2 test-class"
    );
  });
});
