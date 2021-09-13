import AccordionItem from "../../src/components/AccordionItem";
import React from "react";
import { shallow } from "enzyme";

jest.mock("../../src/hooks/useUniqueId");

describe("AccordionItem", () => {
  it("generates id", () => {
    const wrapper = shallow(
      <AccordionItem heading="Test">Hello world</AccordionItem>
    );

    expect(wrapper.find(".usa-accordion__button").prop("aria-controls")).toBe(
      "mock-unique-id"
    );
    expect(wrapper.find(".usa-accordion__content").prop("id")).toBe(
      "mock-unique-id"
    );
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
