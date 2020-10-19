import Status, {
  StatusRow,
} from "../../../../src/pages/employers/claims/status";
import Heading from "../../../../src/components/Heading";
import Lead from "../../../../src/components/Lead";
import React from "react";
import Title from "../../../../src/components/Title";
import shallow from "enzyme/build/shallow";
import { testHook } from "../../../test-utils";
import useAppLogic from "../../../../src/hooks/useAppLogic";

jest.mock("../../../../src/hooks/useAppLogic");

describe("Status", () => {
  let appLogic;
  let wrapper;

  beforeEach(() => {
    testHook(() => {
      appLogic = useAppLogic();
    });

    wrapper = shallow(<Status appLogic={appLogic} />).dive();
  });

  it("renders the page", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("shows the claimant name as the title", () => {
    expect(wrapper.find(Title).childAt(0).text()).toEqual(
      "Notices for Jane Doe"
    );
  });

  it("shows the lead", () => {
    expect(wrapper.find(Lead).childAt(0).text()).toBeTruthy();
  });

  it("shows the appropriate headings", () => {
    const sectionTitles = wrapper
      .find(Heading)
      .map((section) => section.childAt(0).text());
    expect(sectionTitles).toEqual(["Leave details", "Notices"]);
  });

  it("shows the application ID", () => {
    const applicationIdRow = wrapper.find(StatusRow).at(0);
    expect(applicationIdRow.prop("label")).toEqual("Application ID");
    expect(applicationIdRow.childAt(0).text()).toEqual("mock_application_id");
  });

  it("shows the status", () => {
    const statusRow = wrapper.find(StatusRow).at(1);
    expect(statusRow.prop("label")).toEqual("Status");
    expect(statusRow.render().find(".usa-tag").text()).toEqual("Approved");
  });

  it("shows the leave type", () => {
    const leaveTypeRow = wrapper.find(StatusRow).at(2);
    expect(leaveTypeRow.prop("label")).toEqual("Leave type");
    expect(leaveTypeRow.childAt(0).text()).toEqual("Medical leave");
  });

  it("shows the leave duration", () => {
    const leaveDurationRow = wrapper.find(StatusRow).at(3);
    expect(leaveDurationRow.prop("label")).toEqual("Leave duration");
    expect(leaveDurationRow.childAt(0).text()).toEqual("1/1/2021 – 6/1/2021");
  });

  it("shows the relevant documents", () => {
    const relevantDocumentsDiv = wrapper.find("div").last();
    expect(relevantDocumentsDiv.childAt(0).text()).toEqual(
      "Benefit determination notice (PDF)"
    );
    expect(relevantDocumentsDiv.childAt(1).text()).toEqual("Posted 1/22/2021");
  });
});
