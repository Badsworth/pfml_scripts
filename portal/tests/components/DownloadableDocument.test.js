import Document, { DocumentType } from "../../src/models/Document";
import { render, screen } from "@testing-library/react";
import DownloadableDocument from "../../src/components/DownloadableDocument";
import Icon from "../../src/components/Icon";
import React from "react";
import userEvent from "@testing-library/user-event";

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

function renderComponent(customProps = {}) {
  const props = {
    document: DOCUMENT,
    onDownloadClick: jest.fn(),
    ...customProps,
  };

  return render(<DownloadableDocument {...props} />);
}

describe("DownloadableDocument", () => {
  it("renders document item", () => {
    const { container } = renderComponent();
    expect(container.firstChild).toMatchSnapshot();
  });

  it("renders document display name", () => {
    const displayDocumentName = "display test doc name";
    renderComponent({ displayDocumentName });
    expect(screen.getByRole("button")).toHaveAccessibleName(
      displayDocumentName
    );
  });

  it("renders legal notice name", () => {
    renderComponent({ document: LEGAL_NOTICE });
    expect(screen.getByRole("button")).toHaveAccessibleName(
      "Approval notice (PDF)"
    );
  });

  it("renders notice date", () => {
    renderComponent({ showCreatedAt: true });
    expect(screen.getByText("Posted 4/5/2020")).toBeInTheDocument();
  });

  it("calls download function without absence id when there isn't an absence id", () => {
    const mockDownloadDocument = jest.fn();
    renderComponent({ onDownloadClick: mockDownloadDocument });

    userEvent.click(screen.getByRole("button"));
    expect(mockDownloadDocument).toHaveBeenCalledWith(DOCUMENT);
  });

  it("calls download function with absence id when there is an absence id", () => {
    const mockDownloadDocument = jest.fn();
    renderComponent({
      onDownloadClick: mockDownloadDocument,
      absenceId: "mock-absence-id",
    });

    userEvent.click(screen.getByRole("button"));
    expect(mockDownloadDocument).toHaveBeenCalledWith(
      "mock-absence-id",
      DOCUMENT
    );
  });

  it("renders document with icon and additional classname item", () => {
    const { container } = renderComponent({
      icon: <Icon fill="currentColor" name="file_present" size={3} />,
    });
    expect(container.firstChild).toMatchSnapshot();
  });
});
