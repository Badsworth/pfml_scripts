import React from "react";
import Success from "../../../../src/pages/employers/claims/success";
import { shallow } from "enzyme";

describe("Success", () => {
  it("renders Success page", () => {
    const query = { absence_id: "test-absence-id" };
    const wrapper = shallow(<Success query={query} />);

    expect(wrapper).toMatchSnapshot();
  });
});
