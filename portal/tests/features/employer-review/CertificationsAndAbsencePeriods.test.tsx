import {
  MockEmployerClaimBuilder,
  createAbsencePeriod,
} from "../../test-utils";
import { render, screen, within } from "@testing-library/react";
import CertificationsAndAbsencePeriods from "src/features/employer-review/CertificationsAndAbsencePeriods";
import { DocumentType } from "src/models/Document";
import LeaveReason from "src/models/LeaveReason";
import { Props } from "types/common";
import React from "react";
import { faker } from "@faker-js/faker";

const renderComponent = (
  customProps: Partial<Props<typeof CertificationsAndAbsencePeriods>> = {}
) => {
  const claim = new MockEmployerClaimBuilder().completed().create();
  return render(
    <CertificationsAndAbsencePeriods
      claim={claim}
      documents={[]}
      downloadDocument={jest.fn()}
      {...customProps}
    />
  );
};

/**
 * Additional test coverage for this component is in the page tests
 */
describe("CertificationsAndAbsencePeriods", () => {
  it("renders formatted date range for leave duration", () => {
    renderComponent();
    expect(screen.getByText("1/1/2022 to 7/1/2022")).toBeInTheDocument();
  });

  it("renders Documentation section when documents exist", () => {
    // No documents
    renderComponent();
    expect(screen.queryByText("Documentation")).not.toBeInTheDocument();

    // With documents
    renderComponent({
      documents: [
        {
          content_type: "application/pdf",
          created_at: "2021-01-01",
          description: "",
          document_type: DocumentType.certification[LeaveReason.medical],
          fineos_document_id: faker.datatype.uuid(),
          name: "",
        },
        {
          content_type: "image/jpeg",
          created_at: "2021-02-15",
          description: "",
          document_type: DocumentType.certification[LeaveReason.care],
          fineos_document_id: faker.datatype.uuid(),
          name: "",
        },
      ],
    });

    const documentationHeading = screen.getByText("Documentation");
    const documentListItems = within(
      documentationHeading.parentNode as HTMLElement
    ).getAllByRole("listitem");

    // Medical
    expect(documentListItems[0]).not.toHaveTextContent(
      /View the family relationship/
    );
    // Caring leave
    expect(documentListItems[1]).toHaveTextContent(
      /View the family relationship/
    );
    expect(documentationHeading.parentNode).toMatchSnapshot();
  });

  it("renders an absence periods section for each leave reason", () => {
    const claim = new MockEmployerClaimBuilder().completed().create();
    const reasons = Object.keys(LeaveReason) as Array<keyof typeof LeaveReason>;

    claim.absence_periods = reasons.map((reason) =>
      createAbsencePeriod({
        // Use consistent dates so snapshots remain stable
        absence_period_start_date: "2020-01-01",
        reason: LeaveReason[reason],
      })
    );

    renderComponent({ claim });

    const sections = screen.getAllByTestId("absence periods");
    let headings: HTMLElement[] = [];
    sections.forEach((section) => {
      headings = headings.concat(
        within(section).getAllByRole("heading", { level: 3 })
      );
    });

    expect(headings.map((heading) => heading.textContent))
      .toMatchInlineSnapshot(`
      [
        "Active duty",
        "Bond with a child",
        "Care for a family member",
        "Medical leave",
        "Medical leave for pregnancy or birth",
        "Military family",
      ]
    `);
  });
});
