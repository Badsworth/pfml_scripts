import FileCard from "../../src/components/FileCard";
import React from "react";
import { shallow } from "enzyme";

function render(props) {
  const file = new File(["foo"], "foo.png", { type: "image/png" });

  props = Object.assign(
    {
      heading: "Document 1",
      filename: "foo.jpg",
      file,
      onRemoveClick: jest.fn(),
    },
    props
  );

  const wrapper = shallow(<FileCard {...props} />);

  return {
    props,
    wrapper,
  };
}

describe("FileCard", () => {
  it("renders", () => {
    expect(render().wrapper).toMatchSnapshot();
  });

  it("calls the onRemoveClick handler when the remove button is clicked", () => {
    const { props, wrapper } = render();
    wrapper.find("button").simulate("click");

    expect(props.onRemoveClick).toHaveBeenCalledTimes(1);
  });
});
