import { screen, waitFor } from "@testing-library/react";
import BenefitsApplication from "../../src/models/BenefitsApplication";
import Document from "../../src/models/Document";
import DocumentCollection from "../../src/models/DocumentCollection";
import React from "react";
import { renderPage } from "../test-utils";
import withClaimDocuments from "../../src/hoc/withClaimDocuments";

const mockClaimId = "mock-claim-id";
const mockPageContent = "This is the page.";
const mockLoadingDocumentsText = "Loading documents";

jest.mock("../../src/hooks/useAppLogic");

function setup(
  { addCustomSetup } = {},
  customProps = {
    query: {
      claim_id: mockClaimId,
    },
  }
) {
  const PageComponent = (props) => (
    <div>
      {mockPageContent}
      {props.isLoadingDocuments
        ? mockLoadingDocumentsText
        : props.documents.map((document) => (
            <div key={document.fineos_document_id}>
              {document.fineos_document_id}
            </div>
          ))}
    </div>
  );
  const WrappedComponent = withClaimDocuments(PageComponent);

  renderPage(
    WrappedComponent,
    {
      addCustomSetup,
    },
    customProps
  );
}

describe("withClaimDocuments", () => {
  it("renders page with empty documents and isLoadingDocuments when initially loading state", async () => {
    setup();

    expect(
      await screen.findByText(mockLoadingDocumentsText, { exact: false })
    ).toBeInTheDocument();
  });

  it("requires user to be logged in", async () => {
    let spy;

    setup({
      addCustomSetup: (appLogic) => {
        spy = jest.spyOn(appLogic.auth, "requireLogin");
      },
    });

    await waitFor(() => {
      expect(spy).toHaveBeenCalled();
    });
  });

  it("renders the page with Claim documents when document state is loaded", async () => {
    const mockDocuments = new DocumentCollection([
      new Document({ application_id: mockClaimId, fineos_document_id: 1 }),
      new Document({ application_id: mockClaimId, fineos_document_id: 2 }),
      new Document({ application_id: mockClaimId, fineos_document_id: 3 }),
      new Document({
        // Helps assert the filtering logic within the HOC.
        application_id: "something different",
        fineos_document_id: 4,
      }),
    ]);

    setup({
      addCustomSetup: (appLogic) => {
        appLogic.documents.documents = mockDocuments;
        jest
          .spyOn(appLogic.documents, "hasLoadedClaimDocuments")
          .mockReturnValue(true);
      },
    });

    expect(
      await screen.findByText(mockPageContent, { exact: false })
    ).toBeInTheDocument();

    // Assert that the HOC is passing in the applications as a prop to our page component:
    expect(
      await screen.findByText(mockDocuments.items[0].fineos_document_id, {
        exact: false,
      })
    ).toBeInTheDocument();
    expect(
      await screen.findByText(mockDocuments.items[1].fineos_document_id, {
        exact: false,
      })
    ).toBeInTheDocument();
    expect(
      await screen.findByText(mockDocuments.items[2].fineos_document_id, {
        exact: false,
      })
    ).toBeInTheDocument();
    // This document isn't associated with the current claim
    expect(
      screen.queryByText(mockDocuments.items[3].fineos_document_id, {
        exact: false,
      })
    ).not.toBeInTheDocument();
  });

  // Mostly identical to test above, except testing the scenario where the claim prop is set,
  // instead of the query param
  it("renders the page with Application documents when document state is loaded", async () => {
    const mockDocuments = new DocumentCollection([
      new Document({ application_id: mockClaimId, fineos_document_id: 1 }),
    ]);
    const mockApplication = new BenefitsApplication({
      application_id: mockClaimId,
    });

    setup(
      {
        addCustomSetup: (appLogic) => {
          appLogic.documents.documents = mockDocuments;
          jest
            .spyOn(appLogic.documents, "hasLoadedClaimDocuments")
            .mockReturnValue(true);
        },
      },
      { claim: mockApplication }
    );

    expect(
      await screen.findByText(mockPageContent, { exact: false })
    ).toBeInTheDocument();

    // Assert that the HOC is passing in the applications as a prop to our page component:
    expect(
      await screen.findByText(mockDocuments.items[0].fineos_document_id, {
        exact: false,
      })
    ).toBeInTheDocument();
  });
});
