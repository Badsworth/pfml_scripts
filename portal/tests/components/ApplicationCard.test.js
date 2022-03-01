import { cleanup, render, screen } from "@testing-library/react";
import { ApplicationCard } from "../../src/components/ApplicationCard";
import { DocumentType } from "../../src/models/Document";
import ErrorInfo from "../../src/models/ErrorInfo";
import { MockBenefitsApplicationBuilder } from "../test-utils";
import React from "react";
import User from "../../src/models/User";
import { merge } from "lodash";
import useAppLogic from "../../src/hooks/useAppLogic";

const ApplicationCardWithAppLogic = ({
  // eslint-disable-next-line react/prop-types
  addAppLogicMocks = (appLogic) => {},
  ...otherProps
}) => {
  const appLogic = useAppLogic();
  appLogic.auth.requireLogin = jest.fn();
  appLogic.users.requireUserConsentToDataAgreement = jest.fn();
  appLogic.users.requireUserRole = jest.fn();
  appLogic.users.user = new User({ consented_to_data_sharing: true });

  appLogic.documents.loadAll = jest.fn();
  appLogic.documents.isLoadingClaimDocuments = jest.fn();

  addAppLogicMocks(appLogic);

  const defaultProps = {
    isLoadingDocuments: false,
  };

  const props = merge({}, defaultProps, otherProps);

  return <ApplicationCard appLogic={appLogic} {...props} />;
};

describe("ApplicationCard", () => {
  it("renders In Progress heading and body when application lacks EIN and leave reason", () => {
    const claim = new MockBenefitsApplicationBuilder().create();
    const { container } = render(<ApplicationCardWithAppLogic claim={claim} />);
    expect(container.firstChild).toMatchSnapshot();
  });

  it("only renders the 'submit all parts' text when application lacks EIN", () => {
    let claim = new MockBenefitsApplicationBuilder().create();
    render(<ApplicationCardWithAppLogic claim={claim} />);

    expect(screen.getByText(/Submit all three parts/i)).toBeInTheDocument();
    cleanup();

    claim = new MockBenefitsApplicationBuilder().employed().create();
    render(<ApplicationCardWithAppLogic claim={claim} />);

    expect(
      screen.queryByText(/Submit all three parts/i)
    ).not.toBeInTheDocument();
  });

  it("renders leave reason as heading when set", () => {
    const claim = new MockBenefitsApplicationBuilder()
      .bondingBirthLeaveReason()
      .create();
    render(<ApplicationCardWithAppLogic claim={claim} />);

    expect(
      screen.getByRole("heading", { level: 2 }).textContent
    ).toMatchInlineSnapshot(`"Leave to bond with a child"`);
  });

  it("renders EIN and absence case id when set", () => {
    const claim = new MockBenefitsApplicationBuilder().submitted().create();

    render(<ApplicationCardWithAppLogic claim={claim} />);

    expect(screen.getByText(claim.employer_fein)).toBeInTheDocument();
    expect(screen.getByText(claim.fineos_absence_id)).toBeInTheDocument();
  });

  it("renders status button and Other Actions when status is completed", () => {
    const claim = new MockBenefitsApplicationBuilder().completed().create();
    const { container } = render(<ApplicationCardWithAppLogic claim={claim} />);

    expect(container.firstChild).toMatchSnapshot();
  });

  it.each([
    [
      // "Started"
      new MockBenefitsApplicationBuilder().create(),
      false,
    ],
    [
      // "Submitted"
      new MockBenefitsApplicationBuilder().submitted().create(),
      true,
    ],
    [
      // "Completed"
      new MockBenefitsApplicationBuilder().completed().create(),
      false,
    ],
  ])(
    "only loads documents when status is Submitted",
    (claim, expectDocumentsLoad) => {
      const loadAll = jest.fn();
      render(
        <ApplicationCardWithAppLogic
          addAppLogicMocks={(appLogic) => {
            appLogic.documents.loadAll = loadAll;
            appLogic.documents.isLoadingClaimDocuments = () => true;
          }}
          claim={claim}
          documents={[]}
        />
      );

      if (expectDocumentsLoad) {
        expect(loadAll).toHaveBeenCalledWith(claim.application_id);
        expect(screen.queryByRole("progressbar")).toBeInTheDocument();
      } else {
        expect(loadAll).not.toHaveBeenCalled();
        expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
      }
    }
  );

  it("does not show a spinner if there is a document load error", () => {
    const claim = new MockBenefitsApplicationBuilder().submitted().create();
    const errors = [
      new ErrorInfo({
        name: "DocumentsLoadError",
        meta: {
          application_id: "mock_application_id",
        },
      }),
    ];

    render(
      <ApplicationCardWithAppLogic
        addAppLogicMocks={(appLogic) => {
          appLogic.errors = errors;
        }}
        claim={claim}
        documents={[]}
      />
    );

    expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
  });

  it("doesn't display View notices action if application is Submitted but not Completed", () => {
    const claim = new MockBenefitsApplicationBuilder().submitted().create();
    render(
      <ApplicationCardWithAppLogic
        claim={claim}
        documents={[
          {
            application_id: claim.application_id,
            document_type: DocumentType.appealAcknowledgment,
            fineos_document_id: "mock-document-1",
          },
          {
            application_id: claim.application_id,
            document_type: DocumentType.approvalNotice,
            fineos_document_id: "mock-document-3",
          },
        ]}
      />
    );
    expect(
      screen.queryByRole("button", { name: /View your notices/ })
    ).not.toBeInTheDocument();
  });
});
