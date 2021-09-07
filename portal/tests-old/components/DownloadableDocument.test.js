import Document, { DocumentType } from "../../src/models/Document";
import DownloadableDocument from "../../src/components/DownloadableDocument";
import Icon from "../../src/components/Icon";
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

function render(customProps = {}) {
  const mockDownloadDocument = jest.fn();
  const props = {
    document: DOCUMENT,
    onDownloadClick: mockDownloadDocument,
    ...customProps,
  };

  const component = <DownloadableDocument {...props} />;

  return {
    mockDownloadDocument,
    wrapper: shallow(component),
  };
}

describe("DownloadableDocument", () => {
  it("renders document item", () => {
    const { wrapper } = render();
    expect(wrapper).toMatchSnapshot();
  });

  it("renders document display name", () => {
    const displayDocumentName = "display test doc name";
    const { wrapper } = render({ displayDocumentName });
    expect(wrapper.find("Button").children().text()).toEqual(
      displayDocumentName
    );
  });

  it("renders legal notice name", () => {
    const { wrapper } = render({ document: LEGAL_NOTICE });
    expect(wrapper.find("Button").children().text()).toEqual(
      "Approval notice (PDF)"
    );
  });

  it("renders notice date", () => {
    const { wrapper } = render({ showCreatedAt: true });
    expect(wrapper.find("div").text()).toMatchInlineSnapshot(
      `"Posted 4/5/2020"`
    );
  });

  it("calls download function without absence id when there isn't an absence id", () => {
    const { mockDownloadDocument, wrapper } = render();
    act(() => {
      wrapper.find("Button").simulate("click", {
        preventDefault: jest.fn(),
      });
    });
    expect(mockDownloadDocument).toHaveBeenCalledWith(DOCUMENT);
  });

  it("calls download function with absence id when there is an absence id", () => {
    const { mockDownloadDocument, wrapper } = render({
      absenceId: "mock-absence-id",
    });
    act(() => {
      wrapper.find("Button").simulate("click", {
        preventDefault: jest.fn(),
      });
    });
    expect(mockDownloadDocument).toHaveBeenCalledWith(
      "mock-absence-id",
      DOCUMENT
    );
  });

  it("renders document with icon and additional classname item", () => {
    const { wrapper } = render({
      icon: <Icon fill="currentColor" name="file_present" size={3} />,
    });
    expect(wrapper).toMatchSnapshot();
  });
});
