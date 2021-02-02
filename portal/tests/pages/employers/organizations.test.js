import { renderWithAppLogic, testHook } from "../../test-utils";
import Organizations from "../../../src/pages/employers/organizations";
import React from "react";
import { shallow } from "enzyme";
import useAppLogic from "../../../src/hooks/useAppLogic";

jest.mock("../../../src/hooks/useAppLogic");

describe("Organizations", () => {
  let appLogic, wrapper;

  beforeEach(() => {
    testHook(() => {
      appLogic = useAppLogic();
    });

    wrapper = shallow(<Organizations appLogic={appLogic} />).dive();
  });

  it("renders the page", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("shows the correct empty state", () => {
    ({ wrapper } = renderWithAppLogic(Organizations, {
      diveLevels: 1,
    }));

    expect(wrapper.find("LeaveAdministratorRow").exists()).toBe(false);
  });

  it("displays a table row for each user leave administrator", () => {
    const rows = wrapper.find("LeaveAdministratorRow");
    const titles = rows.map((row) => row.dive().find("span").first().text());
    const eins = rows.map((row) => row.dive().find("td").text());
    expect(titles).toEqual(["Book Bindings 'R Us", "Knitting Castle"]);
    expect(eins).toEqual(["1298391823", "390293443"]);
  });

  it('shows the "Verification required" tag if not verified', () => {
    const row = wrapper.find("LeaveAdministratorRow").first();
    const verificationTag = row.dive().find("Tag");
    expect(verificationTag.prop("label")).toBe("Verification required");
    expect(verificationTag.prop("state")).toBe("warning");
  });

  it('does not show the "Verification required" tag if already verified', () => {
    const row = wrapper.find("LeaveAdministratorRow").last();
    expect(row.dive().find("Tag").exists()).toBe(false);
  });
});
