import FilUploadDetails from "../../src/components/FileUploadDetails";
import React from "react";
import { shallow } from "enzyme";

describe("FileUploadDetails", () => {
  it("renders the details with text", () => {
    const wrapper = shallow(<FilUploadDetails />);

    expect(wrapper).toMatchSnapshot();
  });
});
