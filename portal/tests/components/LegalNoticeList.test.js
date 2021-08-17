import Document, { DocumentType } from "../../src/models/Document";
import LegalNoticeList from "../../src/components/LegalNoticeList";
import React from "react";
import { act } from "react-dom/test-utils";
import { shallow } from "enzyme";

const DOCUMENT = new Document({
  content_type: "image/png",
  created_at: "2020-04-05",
  document_type: DocumentType.certification.medicalCertification,
  fineos_document_id: "fineos-id-4",
  name: "Medical cert doc",
});

const LEGAL_NOTICE = new Document({
  content_type: "image/png",
  created_at: "2020-04-05",
  document_type: DocumentType.approvalNotice,
  fineos_document_id: "fineos-id-4",
  name: "legal notice",
});

function render(customProps = { documents: [] }) {
  const mockDownloadDocument = jest.fn();
  const props = {
    onDownloadClick: mockDownloadDocument,
    ...customProps,
  };

  const component = <LegalNoticeList {...props} />;

  return {
    mockDownloadDocument,
    wrapper: shallow(component),
  };
}

describe("LegalNoticeList", () => {
  it("renders only document that are of type legal notice", () => {
    const { wrapper } = render({ documents: [DOCUMENT, LEGAL_NOTICE] });
    expect(wrapper).toMatchSnapshot();
  });

  it("renders fallbacktext if there is no list of documents", () => {
    const { wrapper } = render();
    expect(wrapper.find("p").children()).toMatchInlineSnapshot(
      `"Once we’ve made a decision, you can download the decision notice here. You’ll also get an email notification."`
    );
  });

  it("calls download function on click", () => {
    const onDownloadClick = jest.fn();
    const { wrapper } = render({
      documents: [LEGAL_NOTICE],
      onDownloadClick,
    });
    act(() => {
      wrapper
        .find("DownloadableDocument")
        .dive()
        .find("Button")
        .simulate("click", {
          preventDefault: jest.fn(),
        });
      expect(onDownloadClick).toHaveBeenCalledWith(LEGAL_NOTICE);
    });
  });
});
