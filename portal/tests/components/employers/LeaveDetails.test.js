import Document, { DocumentType } from "../../../src/models/Document";
import { render, screen } from "@testing-library/react";
import AppErrorInfo from "../../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../../src/models/AppErrorInfoCollection";
import LeaveDetails from "../../../src/components/employers/LeaveDetails";
import { MockEmployerClaimBuilder } from "../../test-utils";
import React from "react";
import userEvent from "@testing-library/user-event";

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
      appErrors={new AppErrorInfoCollection()}
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

  it("renders formatted date range for leave duration", () => {
    renderComponent();
    expect(screen.getByText("1/1/2021 to 7/1/2021")).toBeInTheDocument();
  });

  it("renders dash for leave duration if intermittent leave", () => {
    const claimWithIntermittentLeave = new MockEmployerClaimBuilder()
      .completed(true)
      .create();
    renderComponent({ claim: claimWithIntermittentLeave });
    expect(screen.getByText("—")).toBeInTheDocument();
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

  it("renders the relationship question", () => {
    renderComponent({
      claim: claimWithCaringLeave,
    });
    expect(
      screen.getByRole("group", {
        name: "Do you believe the listed relationship is described accurately? (Optional)",
      })
    ).toBeInTheDocument();
  });

  it("initially renders with all conditional comment boxes hidden", () => {
    renderComponent({
      claim: claimWithCaringLeave,
    });
    expect(
      screen.queryByRole("textbox", {
        name: "Tell us why you think this relationship is inaccurate.",
      })
    ).not.toBeInTheDocument();
  });

  it("calls onChangeBelieveRelationshipAccurate when user changes the relation answer", () => {
    const onChangeMock = jest.fn();
    renderComponent({
      claim: claimWithCaringLeave,
      onChangeBelieveRelationshipAccurate: onChangeMock,
    });

    userEvent.click(screen.getByRole("radio", { name: "I don't know" }));

    expect(onChangeMock).toHaveBeenCalledWith("Unknown");
  });

  it("renders the comment box and the alert when user indicates the relationship is inaccurate ", () => {
    renderComponent({
      claim: claimWithCaringLeave,
      believeRelationshipAccurate: "No",
    });

    expect(
      screen.getByRole("textbox", {
        name: "Tell us why you think this relationship is inaccurate.",
      })
    ).toBeInTheDocument();
    expect(screen.getByRole("region")).toMatchSnapshot();
  });

  it("calls onChangeRelationshipInaccurateReason when user leaves a comment", () => {
    const onChangeMock = jest.fn();
    renderComponent({
      claim: claimWithCaringLeave,
      believeRelationshipAccurate: "No",
      onChangeRelationshipInaccurateReason: onChangeMock,
    });

    userEvent.type(screen.getByRole("textbox"), "This is a comment");

    expect(onChangeMock).toHaveBeenCalledWith("This is a comment");
  });

  it("renders the alert info when user indicates the relationship status is unknown ", () => {
    renderComponent({
      claim: claimWithCaringLeave,
      believeRelationshipAccurate: "Unknown",
    });

    expect(screen.getByRole("region")).toMatchSnapshot();
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
    renderComponent({
      claim: claimWithCaringLeave,
      believeRelationshipAccurate: "No",
      appErrors,
    });

    expect(
      screen.getByRole("textbox", {
        name: "Tell us why you think this relationship is inaccurate.",
      })
    ).toHaveClass("usa-input--error");
  });
});
