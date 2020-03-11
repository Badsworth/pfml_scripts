import "../../../src/i18n";
import * as nextRouter from "next/router";
import React from "react";
import Result from "../../../src/pages/eligibility/result";
import { mount } from "enzyme";
jest.mock("next/router");

describe("Result", () => {
  it("renders Spinner before eligibility result", () => {
    nextRouter.useRouter.mockReturnValue({
      query: {
        employeeId: "eef93e5b-7b89-4b08-8e10-8e3ed40b8935",
      },
    });
    const wrapper = mount(<Result />);
    expect(wrapper.exists("Spinner")).toBe(true);
  });

  it("renders Eligible when eligibility result is eligible", () => {
    nextRouter.useRouter.mockReturnValue({
      query: {
        employeeId: "eef93e5b-7b89-4b08-8e10-8e3ed40b8935",
        mockEligibility: "eligible",
      },
    });
    const wrapper = mount(<Result />);
    expect(wrapper.exists("Eligible")).toBe(true);
  });

  it("renders Ineligible when eligibility result is ineligible", () => {
    nextRouter.useRouter.mockReturnValue({
      query: {
        employeeId: "eef93e5b-7b89-4b08-8e10-8e3ed40b8935",
        mockEligibility: "ineligible",
      },
    });
    const wrapper = mount(<Result />);
    expect(wrapper.exists("Ineligible")).toBe(true);
  });

  it("renders Exemption when eligibility result is exempt", () => {
    nextRouter.useRouter.mockReturnValue({
      query: {
        employeeId: "eef93e5b-7b89-4b08-8e10-8e3ed40b8935",
        mockEligibility: "exempt",
      },
    });
    const wrapper = mount(<Result />);
    expect(wrapper.exists("Exemption")).toBe(true);
  });

  it("renders RecordNotFound when eligibility result is notfound", () => {
    nextRouter.useRouter.mockReturnValue({
      query: {
        employeeId: "eef93e5b-7b89-4b08-8e10-8e3ed40b8935",
        mockEligibility: "notfound",
      },
    });
    const wrapper = mount(<Result />);
    expect(wrapper.exists("RecordNotFound")).toBe(true);
  });

  it("returns null when eligibility value is not valid", () => {
    nextRouter.useRouter.mockReturnValue({
      query: {
        employeeId: "eef93e5b-7b89-4b08-8e10-8e3ed40b8935",
        mockEligibility: "error",
      },
    });
    const wrapper = mount(<Result />);
    expect(wrapper.children().length).toEqual(0);
  });
});
