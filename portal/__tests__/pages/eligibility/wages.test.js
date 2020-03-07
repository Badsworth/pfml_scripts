import "../../../src/i18n";
import React from "react";
import Wages from "../../../src/pages/eligibility/wages";
import { mount } from "enzyme";

jest.mock("next/router", () => ({
  useRouter: jest.fn(() => ({
    query: { employeeId: "eef93e5b-7b89-4b08-8e10-8e3ed40b8935" }
  }))
}));

describe("Wages", () => {
  let wrapper;
  beforeEach(() => {
    // mount because shallow does not evaluate useEffect
    wrapper = mount(<Wages />);
  });

  it("renders the page", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("changes radio button with user input", async () => {
    const event = { target: { name: "dataIsCorrect", value: "yes" } };
    wrapper
      .find("input")
      .first()
      .simulate("change", event);

    expect(
      wrapper
        .find("InputChoice")
        .first()
        .prop("checked")
    ).toEqual(true);
  });
});
