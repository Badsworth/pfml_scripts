import Document, { DocumentType } from "../../src/models/Document";
import { render, screen } from "@testing-library/react";
import AppErrorInfo from "../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../src/models/AppErrorInfoCollection";
import { ApplicationCard } from "../../src/components/ApplicationCard";
import { MockBenefitsApplicationBuilder } from "../test-utils";
import React from "react";
import userEvent from "@testing-library/user-event";

const download = jest.fn(() => {
  return Promise.resolve([]);
});

const renderCard = (props) => {
  const defaultProps = {
    appLogic: {
      appErrors: new AppErrorInfoCollection([]),
      documents: {
        download,
      },
    },
    documents: [],
    number: 2,
    claim: new MockBenefitsApplicationBuilder().create(),
    ...props,
  };
  render(<ApplicationCard {...defaultProps} />);
};

describe("ApplicationCard", () => {
  it("uses generic text for main heading when fineos_absence_id is not present", () => {
    renderCard();
    expect(
      screen.getByRole("heading", { name: "Application 2" })
    ).toBeInTheDocument();
  });

  it("doesn't render application details if none present", () => {
    renderCard();
    expect(screen.queryByText(/Employer EIN/)).not.toBeInTheDocument();
    expect(screen.queryByText(/Continuous leave/)).not.toBeInTheDocument();
  });

  it("renders application details, particularly EIN, when present ", () => {
    renderCard({
      claim: new MockBenefitsApplicationBuilder().employed().create(),
    });
    expect(screen.queryByText(/Employer EIN/)).toBeInTheDocument();
    expect(screen.queryByText(/12-3456789/)).toBeInTheDocument();
  });

  it("renders continuous and reduced schedule leave period date ranges", () => {
    renderCard({
      claim: new MockBenefitsApplicationBuilder()
        .reducedSchedule()
        .continuous()
        .create(),
    });
    expect(screen.getByText("1/1/2021 to 6/1/2021")).toBeInTheDocument();
    expect(screen.getByText("Reduced leave schedule")).toBeInTheDocument();
    expect(screen.getByText("2/1/2021 to 7/1/2021")).toBeInTheDocument();
  });

  it("renders Intermittent leave period date range", () => {
    renderCard({
      claim: new MockBenefitsApplicationBuilder().intermittent().create(),
    });
    expect(screen.getByText("2/1/2021 to 7/1/2021")).toBeInTheDocument();
    expect(screen.getByText("Intermittent leave")).toBeInTheDocument();
  });

  it("renders legal notices when needed", () => {
    renderCard({
      claim: new MockBenefitsApplicationBuilder().absenceId().create(),
      documents: [
        new Document({
          application_id: "mock-claim-id",
          document_type: DocumentType.appealAcknowledgment,
        }),
        new Document({
          application_id: "mock-claim-id",
          document_type: DocumentType.approvalNotice,
          fineos_document_id: "mock-document-3",
        }),
        // Throw in a non-legal notice to confirm it doesn't get rendered
        new Document({
          application_id: "mock-claim-id",
          document_type: DocumentType.certification.medicalCertification,
          fineos_document_id: "mock-document-6",
        }),
      ],
    });
    expect(screen.getAllByRole("listitem")).toHaveLength(2);
    expect(
      screen.getByRole("heading", { name: "Download your notices" })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Appeal Acknowledgment (PDF)" })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Approval notice (PDF)" })
    ).toBeInTheDocument();
    expect(download).not.toHaveBeenCalled();
    userEvent.click(
      screen.getByRole("button", { name: "Approval notice (PDF)" })
    );
    expect(download).toHaveBeenCalled();
  });

  it("alerts when there is an err downloading documents", () => {
    const claim = new MockBenefitsApplicationBuilder().completed().create();
    const appLogic = {
      appErrors: new AppErrorInfoCollection([
        new AppErrorInfo({
          meta: { application_id: "mock_application_id" },
          name: "DocumentsLoadError",
        }),
      ]),
    };
    renderCard({ claim, appLogic });
    expect(
      screen.getByText(
        /An error was encountered while checking your application for documents./
      )
    ).toBeInTheDocument();
  });

  it("does not render legal notices section when claim is not submitted", () => {
    renderCard({ claim: new MockBenefitsApplicationBuilder().create() });
    expect(
      screen.queryByRole("heading", { name: "Download your notices" })
    ).not.toBeInTheDocument();
  });

  it("for submitted claims, it shows a link to complete the claim", () => {
    renderCard({
      claim: new MockBenefitsApplicationBuilder().submitted().create(),
    });
    expect(
      screen.getByRole("link", { name: "Continue application" })
    ).toBeInTheDocument();
  });

  it("for submitted claims, it uses case id in header and includes legal notices text", () => {
    renderCard({
      claim: new MockBenefitsApplicationBuilder().submitted().create(),
    });
    expect(
      screen.getByRole("heading", { name: "NTN-111-ABS-01" })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: "Download your notices" })
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        /Once we’ve made a decision, you can download the decision notice here. You’ll also get an email notification./
      )
    ).toBeInTheDocument();
  });

  // TODO (CP-2354) Remove this once there are no submitted claims with null Other Leave data
  it("Can handle submitted claims with null other leave data", () => {
    renderCard({
      claim: new MockBenefitsApplicationBuilder()
        .submitted()
        .medicalLeaveReason()
        .nullOtherLeave()
        .create(),
    });
    expect(screen.getByText(/call the Contact Center/)).toBeInTheDocument();
    expect(
      screen.getByText(/Report any of these situations:/)
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "(833) 344‑7365" })
    ).toBeInTheDocument();
  });

  it("for completed claims, include button for addl documents", () => {
    renderCard({
      claim: new MockBenefitsApplicationBuilder().completed().create(),
    });
    expect(
      screen.getByRole("link", { name: "Upload additional documents" })
    ).toBeInTheDocument();
  });

  it("for completed claims, instructions about reductions are included", () => {
    renderCard({
      claim: new MockBenefitsApplicationBuilder().completed().create(),
    });
    expect(
      screen.getByText(
        /If your plans for other benefits or income during your paid leave have changed, call the Contact Center/
      )
    ).toBeInTheDocument();
  });

  it("can handle bonding claims with no cert docs for births", () => {
    renderCard({
      claim: new MockBenefitsApplicationBuilder()
        .completed()
        .bondingBirthLeaveReason()
        .hasFutureChild()
        .create(),
    });
    expect(
      screen.getByText(/Once your child is born, submit proof of birth/)
    ).toBeInTheDocument();
  });

  it("can handle bonding claims with no cert docs for adoptions", () => {
    renderCard({
      claim: new MockBenefitsApplicationBuilder()
        .completed()
        .bondingAdoptionLeaveReason()
        .hasFutureChild()
        .create(),
    });
    expect(
      screen.getByText(
        /submit proof of placement so that we can make a decision/
      )
    ).toBeInTheDocument();
  });

  it("with a denial notice, users have the option to upload addl documentation", () => {
    const claim = new MockBenefitsApplicationBuilder().submitted().create();
    renderCard({
      claim,
      documents: [
        new Document({
          application_id: claim.application_id,
          created_at: "2021-01-01",
          document_type: DocumentType.denialNotice,
          fineos_document_id: "mock-document-4",
        }),
      ],
    });
    expect(
      screen.getByRole("button", { name: "Denial notice (PDF)" })
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Upload additional documents" })
    ).toBeInTheDocument();
  });

  it("no Continue Application button included when there is a denial notice", () => {
    const claim = new MockBenefitsApplicationBuilder().submitted().create();
    renderCard({
      claim,
      documents: [
        new Document({
          application_id: claim.application_id,
          created_at: "2021-01-01",
          document_type: DocumentType.denialNotice,
          fineos_document_id: "mock-document-4",
        }),
      ],
    });
    expect(
      screen.queryByRole("link", { name: "Continue application" })
    ).not.toBeInTheDocument();
  });
});
