import AddOrganization from "../../../../src/pages/employers/organizations/add-organization";
import React from "react";
import { shallow } from "enzyme";

describe("AddOrganization", () => {
  it("renders page", () => {
    const wrapper = shallow(<AddOrganization />);
    expect(wrapper).toMatchSnapshot();
  });
});
