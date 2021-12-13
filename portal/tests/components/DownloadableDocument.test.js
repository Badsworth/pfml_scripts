import { render, screen } from "@testing-library/react";
import { DocumentType } from "../../src/models/Document";
import DownloadableDocument from "../../src/components/DownloadableDocument";
import Icon from "../../src/components/core/Icon";
import React from "react";
import userEvent from "@testing-library/user-event";

const DOCUMENT = {
  content_type: "image/png",
  created_at: "2020-04-05",
  document_type: DocumentType.certification.medicalCertification,
  fineos_document_id: "fineos-id-4",
  name: "Medical cert doc",
};

const LEGAL_NOTICE = {
  content_type: "image/png",
  created_at: "2020-04-05",
  document_type: DocumentType.approvalNotice,
  fineos_document_id: "fineos-id-4",
  name: "legal notice",
};

const CLAIM_DOCUMENT = {
  content_type: "image/png",
  created_at: "2020-04-05",
  document_type: DocumentType.certification.medicalCertification,
  fineos_document_id: "fineos-id-4",
  name: "Medical cert doc",
};

function renderComponent(customProps = {}) {
  const props = {
    document: DOCUMENT,
    downloadClaimDocument: jest.fn(),
    downloadBenefitsApplicationDocument: jest.fn(),
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
    expect(screen.getByText(/Posted 4\/5\/2020/)).toBeInTheDocument();
  });

  it("calls download function without absence id when there isn't an absence id", () => {
    const mockDownloadDocument = jest.fn();
    renderComponent({
      downloadBenefitsApplicationDocument: mockDownloadDocument,
    });

    userEvent.click(screen.getByRole("button"));
    expect(mockDownloadDocument).toHaveBeenCalledWith(DOCUMENT);
  });

  it("calls download function with absence id when there is an absence id", () => {
    const mockDownloadDocument = jest.fn();
    renderComponent({
      downloadClaimDocument: mockDownloadDocument,
      absenceId: "mock-absence-id",
      document: CLAIM_DOCUMENT,
    });

    userEvent.click(screen.getByRole("button"));
    expect(mockDownloadDocument).toHaveBeenCalledWith(
      DOCUMENT,
      "mock-absence-id"
    );
  });

  it("renders document with icon and additional classname item", () => {
    const { container } = renderComponent({
      icon: <Icon fill="currentColor" name="file_present" size={3} />,
    });
    expect(container.firstChild).toMatchSnapshot();
  });
});
