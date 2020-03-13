import Eligible from "../../src/components/Eligible";
import React from "react";
import { shallow } from "enzyme";

describe("Eligible", () => {
  it("renders Eligible component", () => {
    const wrapper = shallow(<Eligible employeeId="1234" />);

    expect(wrapper).toMatchSnapshot();
  });

  it("changes radio button with user input", () => {
    const event = { target: { name: "dataIsCorrect", value: "yes" } };
    const wrapper = shallow(<Eligible employeeId="1234" />);

    wrapper
      .find("InputChoiceGroup")
      .first()
      .simulate("change", event);

    expect(
      wrapper
        .find("InputChoiceGroup")
        .first()
        .prop("choices")
    ).toMatchInlineSnapshot(`
     Array [
       Object {
         "checked": true,
         "label": "Yes",
         "value": "yes",
       },
       Object {
         "checked": false,
         "label": "No",
         "value": "no",
       },
     ]
     `);
  });
});
