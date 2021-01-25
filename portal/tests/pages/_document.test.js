import Document from "../../src/pages/_document";
import React from "react";
import { shallow } from "enzyme";

describe("Document", () => {
  it("renders the Document", () => {
    const wrapper = shallow(<Document />);

    expect(wrapper).toMatchSnapshot();
  });

  it("blocks search engines in non-prod builds", () => {
    process.env.BUILD_ENV = "stage";
    let wrapper = shallow(<Document />);

    expect(wrapper.find("meta[name='robots']").prop("content")).toBe("noindex");

    process.env.BUILD_ENV = "prod";
    wrapper = shallow(<Document />);

    expect(wrapper.find("meta[name='robots']").exists()).toBe(false);
  });
});
