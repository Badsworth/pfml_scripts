import { MockClaimBuilder, testHook } from "../../../test-utils";
import Status, {
  StatusRow,
} from "../../../../src/pages/employers/claims/status";
import { mount, shallow } from "enzyme";
import Heading from "../../../../src/components/Heading";
import Lead from "../../../../src/components/Lead";
import React from "react";
import Spinner from "../../../../src/components/Spinner";
import StatusTag from "../../../../src/components/StatusTag";
import Title from "../../../../src/components/Title";
import { act } from "react-dom/test-utils";
import useAppLogic from "../../../../src/hooks/useAppLogic";

jest.mock("../../../../src/hooks/useAppLogic");

describe("Status", () => {
  const claim = new MockClaimBuilder().completed().create();
  const query = { absence_id: "NTN-111-ABS-01" };
  let appLogic;
  let wrapper;

  beforeEach(() => {
    testHook(() => {
      appLogic = useAppLogic();
    });
  });

  describe("while the claim is not loaded", () => {
    it("renders the page with a spinner", () => {
      wrapper = mount(<Status appLogic={appLogic} query={query} />);
      expect(wrapper.exists(Spinner)).toBe(true);
      expect(wrapper).toMatchSnapshot();
    });

    it("makes a call to load claim", () => {
      appLogic.employers.claim = null;

      act(() => {
        wrapper = mount(<Status appLogic={appLogic} query={query} />);
      });

      expect(appLogic.employers.load).toHaveBeenCalled();
    });
  });

  describe("when the claim is loaded", () => {
    describe("via employers fetch", () => {
      it("renders the page without a spinner", () => {
        appLogic.employers.claim = claim;
        act(() => {
          wrapper = mount(<Status appLogic={appLogic} query={query} />);
        });

        wrapper.update();

        expect(wrapper.exists(Spinner)).toBe(false);
      });
    });

    describe("via passed-in prop", () => {
      beforeEach(() => {
        wrapper = shallow(
          <Status retrievedClaim={claim} appLogic={appLogic} query={query} />
        ).dive();
      });

      it("renders the page without a spinner", () => {
        expect(wrapper.exists(Spinner)).toBe(false);
        expect(wrapper).toMatchSnapshot();
      });

      it("shows the claimant name as the title", () => {
        expect(wrapper.find(Title).childAt(0).text()).toEqual(
          "Notices for Jane Doe"
        );
      });

      it("shows the lead", () => {
        expect(wrapper.find(Lead).text()).toBeTruthy();
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
        expect(applicationIdRow.childAt(0).text()).toEqual("NTN-111-ABS-01");
      });

      it("shows the status", () => {
        const statusRow = wrapper.find(StatusRow).at(1);
        expect(statusRow.prop("label")).toEqual("Status");
        expect(statusRow.find(StatusTag).prop("state")).toEqual("approved");
      });

      it("shows the leave type", () => {
        const leaveTypeRow = wrapper.find(StatusRow).at(2);
        expect(leaveTypeRow.prop("label")).toEqual("Leave type");
        expect(leaveTypeRow.childAt(0).text()).toEqual("Medical leave");
      });

      it("shows the leave duration", () => {
        const leaveDurationRow = wrapper.find(StatusRow).at(3);
        expect(leaveDurationRow.prop("label")).toEqual("Leave duration");
        expect(leaveDurationRow.childAt(0).text()).toEqual(
          "1/1/2021 – 6/1/2021"
        );
      });

      it("shows the relevant documents", () => {
        const relevantDocumentsDiv = wrapper.find("div").last();
        expect(relevantDocumentsDiv.childAt(0).text()).toEqual(
          "Benefit determination notice (PDF)"
        );
        expect(relevantDocumentsDiv.childAt(1).text()).toEqual(
          "Posted 1/22/2021"
        );
      });
    });
  });
});
