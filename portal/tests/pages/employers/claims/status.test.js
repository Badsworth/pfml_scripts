import {
  MockEmployerClaimBuilder,
  renderWithAppLogic,
  testHook,
} from "../../../test-utils";
import Status from "../../../../src/pages/employers/claims/status";
import { Trans } from "react-i18next";
import useAppLogic from "../../../../src/hooks/useAppLogic";

jest.mock("../../../../src/hooks/useAppLogic");

describe("Status", () => {
  const claim = new MockEmployerClaimBuilder().completed().create();
  const query = { absence_id: "NTN-111-ABS-01" };
  let appLogic;
  let wrapper;

  beforeEach(() => {
    testHook(() => {
      appLogic = useAppLogic();
    });
    appLogic.employers.claim = claim;

    ({ wrapper } = renderWithAppLogic(Status, {
      employerClaimAttrs: claim,
      props: {
        appLogic,
        query,
      },
    }));
  });

  it("renders the page and correct content in Trans component", () => {
    expect(wrapper).toMatchSnapshot();
    expect(wrapper.find(Trans)).toMatchSnapshot();
  });

  it("shows the claimant name as the title", () => {
    expect(wrapper.find("Title").childAt(0).text()).toEqual(
      "Notices for Jane Doe"
    );
  });

  it("shows the lead", () => {
    expect(wrapper.find("Lead").text()).toBeTruthy();
  });

  it("shows the appropriate headings", () => {
    const sectionTitles = wrapper
      .find("Heading")
      .map((section) => section.childAt(0).text());
    expect(sectionTitles).toEqual(["Leave details", "Notices"]);
  });

  it("shows the application ID", () => {
    const applicationIdRow = wrapper.find("StatusRow").at(0);
    expect(applicationIdRow.prop("label")).toEqual("Application ID");
    expect(applicationIdRow.childAt(0).text()).toEqual("NTN-111-ABS-01");
  });

  it("shows the status", () => {
    const statusRow = wrapper.find("StatusRow").at(1);
    expect(statusRow.prop("label")).toEqual("Status");
    expect(statusRow.find("StatusTag").prop("state")).toEqual("approved");
  });

  it("shows the leave type", () => {
    const leaveTypeRow = wrapper.find("StatusRow").at(2);
    expect(leaveTypeRow.prop("label")).toEqual("Leave type");
    expect(leaveTypeRow.childAt(0).text()).toEqual("Medical leave");
  });

  it("shows the leave duration", () => {
    const leaveDurationRow = wrapper.find("StatusRow").at(3);
    expect(leaveDurationRow.prop("label")).toEqual("Leave duration");
    expect(leaveDurationRow.childAt(0).text()).toEqual("1/1/2021 – 7/1/2021");
  });

  it("shows the relevant documents", () => {
    const relevantDocumentsDiv = wrapper.find("div").last();
    expect(relevantDocumentsDiv.childAt(0).text()).toEqual(
      "Benefit determination notice (PDF)"
    );
    expect(relevantDocumentsDiv.childAt(1).text()).toEqual("Posted 1/22/2021");
  });
});
