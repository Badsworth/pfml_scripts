import "../../../src/i18n";
import React from "react";
import Wages from "../../../src/pages/eligibility/wages";
import { mount } from "enzyme";

jest.mock("next/router", () => ({
  useRouter: jest.fn(() => ({
    query: { employeeId: "eef93e5b-7b89-4b08-8e10-8e3ed40b8935" },
  })),
}));

describe("Wages", () => {
  it("renders the page", () => {
    // mount because shallow does not evaluate useEffect
    const wrapper = mount(<Wages />);

    expect(wrapper).toMatchSnapshot();
  });
});
