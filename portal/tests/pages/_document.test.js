import Document from "../../src/pages/_document";
import React from "react";
import { shallow } from "enzyme";

describe("Document", () => {
  it("renders the Document", () => {
    const wrapper = shallow(<Document />);

    expect(wrapper).toMatchSnapshot();
  });
});
