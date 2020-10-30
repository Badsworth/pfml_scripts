import Confirmation from "../../../../src/pages/employers/claims/confirmation";
import React from "react";
import { shallow } from "enzyme";

describe("Confirmation", () => {
  it("renders Confirmation page", () => {
    const query = { absence_id: "test-absence-id", due_date: "2022-01-01" };
    const wrapper = shallow(<Confirmation query={query} />);

    expect(wrapper).toMatchSnapshot();
  });
});
