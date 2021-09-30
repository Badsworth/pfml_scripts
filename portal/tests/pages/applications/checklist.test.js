import Document, { DocumentType } from "../../../src/models/Document";
import { MockBenefitsApplicationBuilder, renderPage } from "../../test-utils";
import { Checklist } from "../../../src/pages/applications/checklist";
import LeaveReason from "../../../src/models/LeaveReason";
import { mockRouter } from "next/router";
import { screen } from "@testing-library/react";

const renderChecklist = (claim, warnings, customProps) => {
  if (!claim) {
    claim = new MockBenefitsApplicationBuilder().create();
  }
  if (!warnings) {
    warnings = [
      {
        field: "first_name",
        message: "first_name is required",
        type: "required",
      },
    ];
  }
  const options = {
    addCustomSetup: (appLogic) => {
      appLogic.benefitsApplications.warningsLists = {
        mock_application_id: warnings,
      };
    },
  };
  const props = {
    query: { claim_id: "mock_application_id" },
    claim,
    documents: [],
    ...customProps,
  };
  return renderPage(Checklist, options, props);
};

describe("Checklist", () => {
  beforeEach(() => {
    mockRouter.pathname = "/applications/checklist";
  });

  it("renders multiple steps", () => {
    const { container } = renderChecklist();
    expect(container).toMatchSnapshot();
    expect(screen.getByText("Part 1")).toBeInTheDocument();
    expect(screen.getByText("Part 1")).toBeInTheDocument();
    expect(screen.getByText("Part 3")).toBeInTheDocument();
  });

  it("initially only the first CTA is enabled and verify id description is displayed", () => {
    renderChecklist();
    expect(
      screen.getByText(
        /You can use a variety of documents to verify your identity, but it’s easiest if you have a Massachusetts driver’s license or Massachusetts Identification Card./
      )
    ).toBeInTheDocument();
    expect(screen.getAllByRole("listitem")).toHaveLength(3);
    expect(
      screen.getByText(/Your name as it appears on your ID./)
    ).toBeInTheDocument();
    const start = screen.getByRole("link", {
      name: "Start: Verify your identification",
    });
    expect(start).toHaveClass("usa-button");
  });

  it("other CTA options are disabled", () => {
    renderChecklist();
    expect(
      screen.getByRole("button", {
        name: "Start: Enter employment information",
      })
    ).toBeDisabled();
    expect(
      screen.getByRole("button", {
        name: "Start: Enter leave details",
      })
    ).toBeDisabled();
    expect(
      screen.getByRole("button", {
        name: "Start: Report other leave, benefits, and income",
      })
    ).toBeDisabled();
    expect(
      screen.getByRole("button", {
        name: "Review and submit application",
      })
    ).toBeDisabled();
  });

  it("On click start, user would be routed to expected destination", () => {
    renderChecklist();
    expect(
      screen.getByRole("link", {
        name: "Start: Verify your identification",
      })
    ).toHaveAttribute(
      "href",
      "/applications/name?claim_id=mock_application_id"
    );
  });

  it("when verify your id is submitted, next section renders as expected", () => {
    const warnings = [
      {
        field: "employment_status",
        message: "employment_status is required",
        type: "required",
      },
      {
        field: "leave_details.employer_notified",
        message: "leave_details.employer_notified is required",
        type: "required",
      },
      {
        field: "work_pattern.work_pattern_type",
        message: "work_pattern.work_pattern_type is required",
        type: "required",
      },
    ];
    renderChecklist(new MockBenefitsApplicationBuilder().create(), warnings);
    expect(screen.getByText(/Completed/)).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Edit: Verify your identification" })
    ).toBeInTheDocument();
    expect(
      screen.getByText("The date you told your employer you were taking leave.")
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", {
        name: "Start: Enter employment information",
      })
    ).toHaveAttribute(
      "href",
      "/applications/employment-status?claim_id=mock_application_id"
    );
    expect(
      screen.getByRole("link", {
        name: "Start: Enter employment information",
      })
    ).toBeEnabled();
  });

  describe("Part 2", () => {
    beforeEach(() => {
      const warnings = [];
      const customProps = {
        query: {
          claim_id: "mock_application_id",
          "part-one-submitted": "true",
        },
      };
      renderChecklist(
        new MockBenefitsApplicationBuilder().submitted().create(),
        warnings,
        customProps
      );
    });

    it("renders alert", () => {
      expect(
        screen.getByText(/Part 1 of your application was confirmed./)
      ).toBeInTheDocument();
      expect(screen.getByText(/Your application ID is/)).toBeInTheDocument();
    });

    it("renders prior steps in black", () => {
      for (let step = 1; step <= 5; step++) {
        expect(screen.getByText(step)).toHaveClass("bg-black");
      }
    });

    it("renders payment heading and description", () => {
      expect(
        screen.getByText("Enter your payment information")
      ).toBeInTheDocument();
      expect(
        screen.getByText(/Tell us how you want to receive payment./)
      ).toBeInTheDocument();
      expect(
        screen.getByRole("link", { name: "Start: Add payment information" })
      ).toBeInTheDocument();
    });

    it("CTA would direct user to expected location", () => {
      expect(
        screen.getByRole("link", { name: "Start: Add payment information" })
      ).toBeEnabled();
      expect(
        screen.getByRole("link", { name: "Start: Add payment information" })
      ).toHaveAttribute(
        "href",
        "/applications/payment-method?claim_id=mock_application_id"
      );
    });
  });

  describe("Part 3", () => {
    beforeEach(() => {
      const warnings = [];
      const customProps = {
        query: {
          claim_id: "mock_application_id",
          "payment-pref-submitted": "true",
        },
      };
      renderChecklist(
        new MockBenefitsApplicationBuilder()
          .complete()
          .directDeposit()
          .create(),
        warnings,
        customProps
      );
    });

    it("renders alert that Part 2 is confirmed", () => {
      expect(
        screen.getByText(/Part 2 of your application was confirmed./)
      ).toBeInTheDocument();
      expect(
        screen.getByText(
          /Now, you can work on Part 3, and submit your application./
        )
      ).toBeInTheDocument();
    });

    it("renders prior step in black", () => {
      for (let step = 1; step <= 6; step++) {
        expect(screen.getByText(step)).toHaveClass("bg-black");
      }
    });

    it("renders documents heading and description", () => {
      expect(screen.getByText("Upload your documents")).toBeInTheDocument();
      expect(
        screen.getByText(
          /Upload proof of identity. If you entered a Massachusetts driver’s license or Mass ID number in step 1, upload the same ID./
        )
      ).toBeInTheDocument();
      expect(
        screen.getByRole("link", {
          name: "Start: Upload identification document",
        })
      ).toBeInTheDocument();
      expect(
        screen.getByRole("link", { name: "fax or mail documents" })
      ).toBeInTheDocument();
      expect(
        screen.getByRole("link", {
          name: "Certification of Your Serious Health Condition",
        })
      ).toBeInTheDocument();
    });

    it("renders two CTA options that would direct to expected locations", () => {
      expect(
        screen.getByRole("link", {
          name: "Start: Upload identification document",
        })
      ).toBeEnabled();
      expect(
        screen.getByRole("link", {
          name: "Start: Upload leave certification documents",
        })
      ).toBeEnabled();
      expect(
        screen.getByRole("link", {
          name: "Start: Upload identification document",
        })
      ).toHaveAttribute(
        "href",
        "/applications/upload-id?claim_id=mock_application_id"
      );
      expect(
        screen.getByRole("link", {
          name: "Start: Upload leave certification documents",
        })
      ).toHaveAttribute(
        "href",
        "/applications/upload-certification?claim_id=mock_application_id"
      );
    });
  });

  describe("Part 3, varied leave reasons", () => {
    it("renders proper description for leave reason bonding new born", () => {
      const warnings = [];
      const customProps = {
        query: {
          claim_id: "mock_application_id",
          "payment-pref-submitted": "true",
        },
      };
      renderChecklist(
        new MockBenefitsApplicationBuilder()
          .complete()
          .directDeposit()
          .bondingBirthLeaveReason()
          .create(),
        warnings,
        customProps
      );
      expect(
        screen.getByText(
          /You need to provide your child’s birth certificate or a document from a health care provider that shows the child’s date of birth./
        )
      ).toBeInTheDocument();
    });

    it("renders proper description for leave reason adoptions", () => {
      const warnings = [];
      const customProps = {
        query: {
          claim_id: "mock_application_id",
          "payment-pref-submitted": "true",
        },
      };
      renderChecklist(
        new MockBenefitsApplicationBuilder()
          .complete()
          .directDeposit()
          .bondingAdoptionLeaveReason()
          .create(),
        warnings,
        customProps
      );
      expect(
        screen.getByText(
          /You need to provide a statement confirming the placement and the date of placement./
        )
      ).toBeInTheDocument();
    });

    it("renders proper description for leave reason medical", () => {
      const warnings = [];
      const customProps = {
        query: {
          claim_id: "mock_application_id",
          "payment-pref-submitted": "true",
        },
      };
      renderChecklist(
        new MockBenefitsApplicationBuilder()
          .complete()
          .directDeposit()
          .medicalLeaveReason()
          .create(),
        warnings,
        customProps
      );
      expect(
        screen.getByText(/You need to provide your completed/)
      ).toBeInTheDocument();
    });

    it("renders proper description for leave reason care", () => {
      const warnings = [];
      const customProps = {
        query: {
          claim_id: "mock_application_id",
          "payment-pref-submitted": "true",
        },
      };
      renderChecklist(
        new MockBenefitsApplicationBuilder()
          .complete()
          .directDeposit()
          .caringLeaveReason()
          .create(),
        warnings,
        customProps
      );
      expect(
        screen.getByText(/You need to provide your completed/)
      ).toBeInTheDocument();
      expect(
        screen.getByRole("link", {
          name: "Certification of Your Family Member’s Serious Health Condition",
        })
      ).toBeInTheDocument();
    });
  });
  describe("Submit", () => {
    it("enables Review and Submit once all portions are completed", () => {
      const warnings = [];
      const customProps = {
        documents: [
          new Document({
            application_id: "mock-claim-id",
            document_type: DocumentType.certification[LeaveReason.pregnancy],
          }),
          new Document({
            application_id: "mock-claim-id",
            document_type: DocumentType.identityVerification,
          }),
        ],
      };
      renderChecklist(
        new MockBenefitsApplicationBuilder()
          .complete()
          .pregnancyLeaveReason()
          .create(),
        warnings,
        customProps
      );
      expect(
        screen.getByRole("link", { name: "Review and submit application" })
      ).toBeEnabled();
      expect(
        screen.getByRole("link", { name: "Review and submit application" })
      ).toHaveAttribute(
        "href",
        "/applications/review?claim_id=mock_application_id"
      );
    });

    it("does not enable Review and Submit when there is a document type mismatch", () => {
      const warnings = [];
      const customProps = {
        documents: [
          new Document({
            application_id: "mock-claim-id",
            document_type: DocumentType.certification[LeaveReason.pregnancy],
          }),
          new Document({
            application_id: "mock-claim-id",
            document_type: DocumentType.identityVerification,
          }),
        ],
      };
      renderChecklist(
        new MockBenefitsApplicationBuilder()
          .complete()
          .caringLeaveReason()
          .create(),
        warnings,
        customProps
      );
      expect(
        screen.getByRole("button", { name: "Review and submit application" })
      ).toBeDisabled();
    });
  });
});
