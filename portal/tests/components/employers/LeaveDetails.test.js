import { render, screen } from "@testing-library/react";
import { DocumentType } from "../../../src/models/Document";
import LeaveDetails from "../../../src/components/employers/LeaveDetails";
import { MockEmployerClaimBuilder } from "../../test-utils";
import React from "react";
import userEvent from "@testing-library/user-event";

const DOCUMENTS = [
  {
    content_type: "image/png",
    created_at: "2020-04-05",
    document_type: DocumentType.certification.medicalCertification,
    fineos_document_id: "fineos-id-4",
    name: "Medical cert doc",
  },
  {
    content_type: "application/pdf",
    created_at: "2020-02-01",
    document_type: DocumentType.certification.medicalCertification,
    fineos_document_id: "fineos-id-9",
    // intentionally omit name
  },
];

const claimWithCaringLeave = new MockEmployerClaimBuilder()
  .completed()
  .caringLeaveReason()
  .create();

const renderComponent = (props = {}) => {
  const claim = new MockEmployerClaimBuilder().completed().create();
  return render(
    <LeaveDetails
      claim={claim}
      documents={[]}
      downloadDocument={jest.fn()}
      appErrors={[]}
      {...props}
    />
  );
};

describe("LeaveDetails", () => {
  it("renders the component", () => {
    const { container } = renderComponent();
    expect(container).toMatchSnapshot();
  });

  it("does not render relationship question when claim is not for Care", () => {
    renderComponent();
    expect(
      screen.queryByRole("group", {
        name: "Do you believe the listed relationship is described accurately? (Optional)",
      })
    ).not.toBeInTheDocument();
  });

  it("renders leave reason as link when reason is not pregnancy", () => {
    renderComponent();
    expect(
      screen.getByRole("link", { name: "Medical leave" })
    ).toBeInTheDocument();
  });

  it("does not render leave reason as link when reason is pregnancy", () => {
    const claimWithPregnancyLeave = new MockEmployerClaimBuilder()
      .completed()
      .pregnancyLeaveReason()
      .create();
    renderComponent({ claim: claimWithPregnancyLeave });

    expect(screen.queryByRole("link")).not.toBeInTheDocument();
    expect(
      screen.getByText("Medical leave for pregnancy or birth")
    ).toBeInTheDocument();
  });

  it("renders formatted leave reason as sentence case", () => {
    renderComponent();
    expect(screen.getByText("Medical leave")).toBeInTheDocument();
  });

  it("`renders formatted date range for leave duration`", () => {
    renderComponent();
    expect(screen.getByText("1/1/2022 to 7/1/2022")).toBeInTheDocument();
  });

  it("does not render documentation row", () => {
    renderComponent();
    expect(
      screen.queryByRole("heading", { name: "Documentation" })
    ).not.toBeInTheDocument();
  });

  it("shows the documents heading when there are documents", () => {
    renderComponent({ documents: DOCUMENTS, downloadDocument: jest.fn() });
    expect(
      screen.getByRole("heading", { name: "Documentation" })
    ).toBeInTheDocument();
  });

  it("renders documentation hint correctly without family relationship", () => {
    renderComponent({ documents: DOCUMENTS, downloadDocument: jest.fn() });
    expect(
      screen.queryByText(/View the family relationship on page 3./)
    ).not.toBeInTheDocument();
  });

  it("displays the generic document name", () => {
    renderComponent({ documents: DOCUMENTS, downloadDocument: jest.fn() });
    expect(
      screen.getAllByRole("button", {
        name: "Your employee's certification document",
      })
    ).toHaveLength(2);
  });

  it("makes a call to download documents on click", () => {
    const downloadDocumentSpy = jest.fn();
    renderComponent({
      documents: DOCUMENTS,
      downloadDocument: downloadDocumentSpy,
    });
    userEvent.click(screen.getAllByRole("button")[0]);

    expect(downloadDocumentSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        content_type: "image/png",
        created_at: "2020-04-05",
        document_type: "State managed Paid Leave Confirmation",
        fineos_document_id: "fineos-id-4",
        name: "Medical cert doc",
      }),
      "NTN-111-ABS-01"
    );
  });

  it("renders documentation hint correctly with family relationship", () => {
    renderComponent({
      claim: claimWithCaringLeave,
      documents: DOCUMENTS,
      downloadDocument: jest.fn(),
    });
    expect(
      screen.getByText(/View the family relationship on page 3./)
    ).toBeInTheDocument();
  });
});
