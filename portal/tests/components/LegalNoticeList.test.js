import Document, { DocumentType } from "../../src/models/Document";
import { render, screen } from "@testing-library/react";
import LegalNoticeList from "../../src/components/LegalNoticeList";
import React from "react";
import userEvent from "@testing-library/user-event";

const CERT_DOCUMENT = new Document({
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

function renderComponent(customProps = { documents: [] }) {
  const mockDownloadDocument = jest.fn();
  const props = {
    onDownloadClick: mockDownloadDocument,
    ...customProps,
  };

  return render(<LegalNoticeList {...props} />);
}

describe("LegalNoticeList", () => {
  it("renders only documents that are legal notices", () => {
    const { container } = renderComponent({
      documents: [CERT_DOCUMENT, LEGAL_NOTICE],
    });
    expect(container).toMatchSnapshot();
  });

  it("does not render anything if there are no relevant documents", () => {
    const { container } = renderComponent();

    expect(container).toBeEmptyDOMElement();
  });

  it("calls download function on click", () => {
    const onDownloadClick = jest.fn();

    renderComponent({
      documents: [LEGAL_NOTICE],
      onDownloadClick,
    });
    userEvent.click(
      screen.getByRole("button", { name: "Approval notice (PDF)" })
    );

    expect(onDownloadClick).toHaveBeenCalledWith(LEGAL_NOTICE);
  });
});
