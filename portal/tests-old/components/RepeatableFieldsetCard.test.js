import React from "react";
import RepeatableFieldsetCard from "../../src/components/RepeatableFieldsetCard";
import { shallow } from "enzyme";

describe("RepeatableFieldsetCard", () => {
  let props;

  beforeEach(() => {
    props = {
      className: "custom-class-name",
      entry: { first_name: "Bud" },
      heading: "Person",
      index: 0,
      removeButtonLabel: "Remove",
      onRemoveClick: jest.fn(),
    };
  });

  it("renders with the given content", () => {
    const wrapper = shallow(
      <RepeatableFieldsetCard {...props}>
        <p>Hello world</p>
      </RepeatableFieldsetCard>
    );

    expect(wrapper).toMatchSnapshot();
  });

  describe("when showRemoveButton is true", () => {
    let wrapper;

    beforeEach(() => {
      props.showRemoveButton = true;

      wrapper = shallow(
        <RepeatableFieldsetCard {...props}>
          <p>Hello world</p>
        </RepeatableFieldsetCard>
      );
    });

    it("shows the remove button", () => {
      expect(wrapper.find("Button")).toMatchSnapshot();
    });

    it("calls the onRemoveClick handler when the remove button is clicked", () => {
      wrapper.find("Button").simulate("click");

      expect(props.onRemoveClick).toHaveBeenCalledTimes(1);
    });
  });
});
