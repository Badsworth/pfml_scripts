import Document, { DocumentType } from "../../../src/models/Document";
import {
  MockEmployerClaimBuilder,
  simulateEvents,
  testHook,
} from "../../test-utils";
import AppErrorInfo from "../../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../../src/models/AppErrorInfoCollection";
import LeaveDetails from "../../../src/components/employers/LeaveDetails";
import React from "react";
import { act } from "react-dom/test-utils";
import { shallow } from "enzyme";
import useFunctionalInputProps from "../../../src/hooks/useFunctionalInputProps";

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
  const downloadDocumentSpy = jest.fn();
  const updateFields = jest.fn();
  let claim, getFunctionalInputProps;

  function render(givenProps = {}) {
    claim =
      givenProps.claim || new MockEmployerClaimBuilder().completed().create();
    const defaultProps = {
      claim,
      documents: [],
      downloadDocument: downloadDocumentSpy,
      getFunctionalInputProps,
      updateFields,
    };

    const props = { ...defaultProps, ...givenProps };
    return shallow(<LeaveDetails {...props} />);
  }

  beforeEach(() => {
    testHook(() => {
      getFunctionalInputProps = useFunctionalInputProps({
        appErrors: new AppErrorInfoCollection(),
        formState: {},
        updateFields,
      });
    });
  });

  it("renders the component", () => {
    const wrapper = render();
    expect(wrapper).toMatchSnapshot();
  });

  it("does not render relationship question when claim is not for Care", () => {
    const wrapper = render();
    expect(wrapper.exists("InputChoiceGroup")).toBe(false);
  });

  it("renders leave reason as link when reason is not pregnancy", () => {
    const wrapper = render();
    expect(wrapper.find("ReviewRow[data-test='leave-type']").children())
      .toMatchInlineSnapshot(`
      <a
        href="https://www.mass.gov/info-details/paid-family-and-medical-leave-pfml-benefits-guide#about-medical-leave-"
        rel="noopener"
        target="_blank"
      >
        Medical leave
      </a>
    `);
  });

  it("does not render leave reason as link when reason is pregnancy", () => {
    const claimWithPregnancyLeave = new MockEmployerClaimBuilder()
      .completed()
      .pregnancyLeaveReason()
      .create();
    const wrapper = render({ claim: claimWithPregnancyLeave });

    expect(
      wrapper.find("ReviewRow[data-test='leave-type']").children()
    ).toMatchInlineSnapshot(`"Medical leave for pregnancy or birth"`);
  });

  it("renders formatted leave reason as sentence case", () => {
    const wrapper = render();
    expect(
      wrapper
        .find("ReviewRow[data-test='leave-type']")
        .children()
        .first()
        .text()
    ).toEqual("Medical leave");
  });

  it("renders formatted date range for leave duration", () => {
    const wrapper = render();
    expect(wrapper.find("ReviewRow").last().children().first().text()).toEqual(
      "1/1/2021 to 7/1/2021"
    );
  });

  it("renders dash for leave duration if intermittent leave", () => {
    const claimWithIntermittentLeave = new MockEmployerClaimBuilder()
      .completed(true)
      .create();
    const wrapper = render({ claim: claimWithIntermittentLeave });
    expect(wrapper.find("ReviewRow").last().children().first().text()).toEqual(
      "—"
    );
  });

  it("does not render documentation row", () => {
    const wrapper = render();
    expect(wrapper.exists('ReviewRow[label="Documentation"]')).toBe(false);
  });

  describe("when there are documents", () => {
    const setup = () => {
      const claim = new MockEmployerClaimBuilder().completed().create();
      const wrapper = render({ claim, documents: DOCUMENTS });
      return { wrapper };
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

    it("displays the generic document name", () => {
      const { wrapper } = setup();
      const medicalDocuments = wrapper.find("DownloadableDocument");
      expect(medicalDocuments.length).toBe(2);
      expect(
        medicalDocuments.map((node) =>
          node
            .dive()
            .containsMatchingElement("Your employee's certification document")
        )
      ).toEqual([true, true]);
    });

    it("makes a call to download documents on click", async () => {
      const { wrapper } = setup();
      await act(async () => {
        await wrapper
          .find("DownloadableDocument")
          .at(0)
          .dive()
          .find("Button")
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
      const claim = new MockEmployerClaimBuilder()
        .completed()
        .caringLeaveReason()
        .create();
      const wrapper = render({ ...props, claim, documents });
      const { changeRadioGroup } = simulateEvents(wrapper);
      return {
        changeRadioGroup,
        wrapper,
      };
    };

    it("renders documentation hint correctly with family relationship", () => {
      const { wrapper } = setup(DOCUMENTS);
      const documentsHint = wrapper
        .find(
          'Trans[i18nKey="components.employersLeaveDetails.recordkeepingInstructions"]'
        )
        .dive();
      expect(documentsHint).toMatchSnapshot();
    });

    it("renders the relationship question", () => {
      const { wrapper } = setup();
      expect(wrapper).toMatchSnapshot();
      expect(wrapper.exists("InputChoiceGroup")).toBe(true);
    });

    it("initially renders with all conditional comment boxes hidden", () => {
      const { wrapper } = setup();
      const conditionalContentArray = wrapper.find("ConditionalContent");

      for (const content in conditionalContentArray) {
        expect(content.prop("visible")).toBe(false);
      }
    });

    it("renders the comment box when user indicates the relationship is inaccurate ", () => {
      const { wrapper, changeRadioGroup } = setup();
      changeRadioGroup("believe_relationship_accurate", "No");
      expect(updateFields).toHaveBeenCalledWith({
        believe_relationship_accurate: "No",
      });
      wrapper.setProps({ believeRelationshipAccurate: "No" });

      const relationshipInaccurateElement = wrapper.find(
        "ConditionalContent[data-test='relationship-accurate-no']"
      );
      expect(relationshipInaccurateElement.prop("visible")).toBe(true);
    });

    it("renders the comment box when user indicates the relationship status is unknown ", () => {
      const { wrapper, changeRadioGroup } = setup();
      changeRadioGroup("believe_relationship_accurate", "Unknown");
      expect(updateFields).toHaveBeenCalledWith({
        believe_relationship_accurate: "Unknown",
      });
      wrapper.setProps({ believeRelationshipAccurate: "Unknown" });

      const relationshipUnknownElement = wrapper.find(
        "ConditionalContent[data-test='relationship-accurate-unknown']"
      );
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
      testHook(() => {
        getFunctionalInputProps = useFunctionalInputProps({
          appErrors,
          formState: {},
          updateFields,
        });
      });
      const { wrapper } = setup([], { getFunctionalInputProps });

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
          .find("textarea[name='relationship_inaccurate_reason']")
          .hasClass("usa-input--error")
      ).toEqual(true);
    });
  });
});
