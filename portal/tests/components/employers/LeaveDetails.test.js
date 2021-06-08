import Document, { DocumentType } from "../../../src/models/Document";
import { MockEmployerClaimBuilder, simulateEvents } from "../../test-utils";
import AppErrorInfo from "../../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../../src/models/AppErrorInfoCollection";
import LeaveDetails from "../../../src/components/employers/LeaveDetails";
import React from "react";
import ReviewRow from "../../../src/components/ReviewRow";
import { act } from "react-dom/test-utils";
import { shallow } from "enzyme";

const DOCUMENTS = [
  new Document({
    content_type: "image/png",
    created_at: "2020-04-05",
    document_type: DocumentType.certification.medicalCertification,
    fineos_document_id: "fineos-id-4",
    name: "Medical cert doc",
  }),
  new Document({
    content_type: "application/pdf",
    created_at: "2020-02-01",
    document_type: DocumentType.certification.medicalCertification,
    fineos_document_id: "fineos-id-9",
    // intentionally omit name
  }),
];

describe("LeaveDetails", () => {
  let claim, wrapper;

  beforeEach(() => {
    claim = new MockEmployerClaimBuilder().completed().create();
    wrapper = shallow(
      <LeaveDetails
        claim={claim}
        documents={[]}
        downloadDocument={jest.fn()}
        appErrors={new AppErrorInfoCollection()}
      />
    );
  });

  it("renders the component", () => {
    expect(wrapper).toMatchSnapshot();
  });

  it("does not render relationship question when claim is not for Care", () => {
    expect(wrapper.exists("InputChoiceGroup")).toBe(false);
  });

  it("renders the emergency regs content when claim is for Bonding", () => {
    const bondingClaim = new MockEmployerClaimBuilder()
      .completed()
      .bondingLeaveReason()
      .create();
    const bondingWrapper = shallow(
      <LeaveDetails
        claim={bondingClaim}
        documents={[]}
        downloadDocument={jest.fn()}
        appErrors={new AppErrorInfoCollection()}
      />
    );

    expect(bondingWrapper.find("Details Trans").dive()).toMatchSnapshot();
  });

  it("renders formatted leave reason as sentence case", () => {
    expect(wrapper.find(ReviewRow).first().children().first().text()).toEqual(
      "Medical leave"
    );
  });

  it("renders formatted date range for leave duration", () => {
    expect(wrapper.find(ReviewRow).last().children().first().text()).toEqual(
      "1/1/2021 – 7/1/2021"
    );
  });

  it("renders dash for leave duration if intermittent leave", () => {
    const claimWithIntermittentLeave = new MockEmployerClaimBuilder()
      .completed(true)
      .create();
    const wrapper = shallow(
      <LeaveDetails
        claim={claimWithIntermittentLeave}
        documents={[]}
        downloadDocument={jest.fn()}
        appErrors={new AppErrorInfoCollection()}
      />
    );
    expect(wrapper.find(ReviewRow).last().children().first().text()).toEqual(
      "—"
    );
  });

  it("does not render documentation row", () => {
    expect(wrapper.exists('ReviewRow[label="Documentation"]')).toBe(false);
  });

  describe("when there are documents", () => {
    const setup = () => {
      const downloadDocumentSpy = jest.fn();
      const claim = new MockEmployerClaimBuilder().completed().create();
      const wrapper = shallow(
        <LeaveDetails
          claim={claim}
          documents={DOCUMENTS}
          downloadDocument={downloadDocumentSpy}
          appErrors={new AppErrorInfoCollection()}
        />
      );
      return { downloadDocumentSpy, wrapper };
    };

    it("shows the documents heading", () => {
      const { wrapper } = setup();
      expect(wrapper.exists('ReviewRow[label="Documentation"]')).toBe(true);
    });

    it("renders documentation hint correctly with family relationship", () => {
      const { wrapper } = setup();
      const documentsHint = wrapper
        .find(
          'Trans[i18nKey="components.employersLeaveDetails.recordkeepingInstructions"]'
        )
        .dive();
      expect(documentsHint).toMatchSnapshot();
    });

    it("renders document's name if there is no document name", () => {
      const { wrapper } = setup();
      const medicalDocuments = wrapper.find("HcpDocumentItem");
      expect(medicalDocuments.length).toBe(2);
      expect(medicalDocuments.map((node) => node.dive().text())).toEqual([
        "Medical cert doc",
        "Certification of Your Serious Health Condition",
      ]);
    });

    it("makes a call to download documents on click", async () => {
      const { downloadDocumentSpy, wrapper } = setup();
      await act(async () => {
        await wrapper
          .find("HcpDocumentItem")
          .at(0)
          .dive()
          .find("a")
          .simulate("click", {
            preventDefault: jest.fn(),
          });
      });

      expect(downloadDocumentSpy).toHaveBeenCalledWith(
        "NTN-111-ABS-01",
        expect.objectContaining({
          content_type: "image/png",
          created_at: "2020-04-05",
          document_type: "State managed Paid Leave Confirmation",
          fineos_document_id: "fineos-id-4",
          name: "Medical cert doc",
        })
      );
    });
  });

  describe("Caring Leave", () => {
    const setup = (documents = [], props = {}) => {
      const onChangeBelieveRelationshipAccurateMock = jest.fn();
      const claim = new MockEmployerClaimBuilder()
        .completed()
        .caringLeaveReason()
        .create();
      const wrapper = shallow(
        <LeaveDetails
          claim={claim}
          documents={documents}
          downloadDocument={jest.fn()}
          onChangeBelieveRelationshipAccurate={
            onChangeBelieveRelationshipAccurateMock
          }
          onChangeRelationshipInaccurateReason={jest.fn()}
          appErrors={new AppErrorInfoCollection()}
          {...props}
        />
      );
      const { changeRadioGroup } = simulateEvents(wrapper);
      return {
        changeRadioGroup,
        wrapper,
        onChangeBelieveRelationshipAccurateMock,
      };
    };

    it("does not render relationship question when showCaringLeaveType flag is false", () => {
      const { wrapper } = setup();
      expect(wrapper.exists("InputChoiceGroup")).toBe(false);
    });

    it("renders documentation hint correctly with family relationship", () => {
      const { wrapper } = setup(DOCUMENTS);
      const documentsHint = wrapper
        .find(
          'Trans[i18nKey="components.employersLeaveDetails.recordkeepingInstructions"]'
        )
        .dive();
      expect(documentsHint).toMatchSnapshot();
    });

    it("renders relationship question when showCaringLeaveType flag is true", () => {
      process.env.featureFlags = { showCaringLeaveType: true };
      const { wrapper } = setup();
      expect(wrapper).toMatchSnapshot();
      expect(wrapper.exists("InputChoiceGroup")).toBe(true);
    });

    it("initially renders with all conditional comment boxes hidden", () => {
      const { wrapper } = setup();
      const conditionalContentArray = wrapper.find("ConditionalContent")

      for (const content in conditionalContentArray) {
        expect(content.prop("visible")).toBe(false);
      }
    });

    it("renders the comment box when user indicates the relationship is inaccurate ", () => {
      const {
        wrapper,
        changeRadioGroup,
        onChangeBelieveRelationshipAccurateMock,
      } = setup();
      changeRadioGroup("believeRelationshipAccurate", "No");
      expect(onChangeBelieveRelationshipAccurateMock).toHaveBeenCalledWith(
        "No"
      );
      wrapper.setProps({ believeRelationshipAccurate: "No" });

      const relationshipInaccurateElement = wrapper.find("ConditionalContent[data-test='relationship-accurate-no']")
      expect(relationshipInaccurateElement.prop("visible")).toBe(true);
    });

    it("renders the comment box when user indicates the relationship status is unknown ", () => {
      const {
        wrapper,
        changeRadioGroup,
        onChangeBelieveRelationshipAccurateMock,
      } = setup();
      changeRadioGroup("believeRelationshipAccurate", "Unknown");
      expect(onChangeBelieveRelationshipAccurateMock).toHaveBeenCalledWith(
        "Unknown"
      );
      wrapper.setProps({ believeRelationshipAccurate: "Unknown" });

      const relationshipUnknownElement = wrapper.find("ConditionalContent[data-test='relationship-accurate-unknown']")
      expect(relationshipUnknownElement.prop("visible")).toBe(true);
    });

    it("renders inline error message when the text exceeds the limit", () => {
      const appErrors = new AppErrorInfoCollection([
        new AppErrorInfo({
          field: "relationship_inaccurate_reason",
          type: "maxLength",
          message:
            "Please shorten your comment. We cannot accept comments that are longer than 9999 characters.",
        }),
      ]);
      const { wrapper } = setup([], { appErrors });

      expect(
        wrapper
          .find("ConditionalContent")
          .find("FormLabel")
          .dive()
          .find("span")
          .text()
      ).toMatchInlineSnapshot(
        `"Please shorten your comment. We cannot accept comments that are longer than 9999 characters."`
      );
      expect(
        wrapper
          .find("ConditionalContent")
          .find("textarea[name='relationshipInaccurateReason']")
          .hasClass("usa-input--error")
      ).toEqual(true);
    });
  });
});
