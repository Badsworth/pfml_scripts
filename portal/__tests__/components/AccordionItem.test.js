import AccordionItem from "../../src/components/AccordionItem";
import React from "react";
import { shallow } from "enzyme";
import uniqueId from "lodash/uniqueId";

jest.mock("lodash/uniqueId");

describe("AccordionItem", () => {
  it("generates id", () => {
    uniqueId.mockReturnValueOnce("mock-id");

    const wrapper = shallow(
      <AccordionItem heading="Test">Hello world</AccordionItem>
    );

    expect(wrapper.find(".usa-accordion__button").prop("aria-controls")).toBe(
      "mock-id"
    );
    expect(wrapper.find(".usa-accordion__content").prop("id")).toBe("mock-id");
  });

  it("is collapsed by default", () => {
    const wrapper = shallow(
      <AccordionItem heading="Test">Hello world</AccordionItem>
    );

    expect(wrapper.find(".usa-accordion__button").prop("aria-expanded")).toBe(
      "false"
    );
    expect(wrapper.find(".usa-accordion__content").prop("hidden")).toBe(true);
  });

  it("is expands when clicked", () => {
    const wrapper = shallow(
      <AccordionItem heading="Test">Hello world</AccordionItem>
    );

    wrapper.find(".usa-accordion__button").simulate("click");

    expect(wrapper.find(".usa-accordion__button").prop("aria-expanded")).toBe(
      "true"
    );
    expect(wrapper.find(".usa-accordion__content").prop("hidden")).toBe(false);
  });
});
