import { render, screen } from "@testing-library/react";
import AppErrorInfo from "../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../src/models/AppErrorInfoCollection";
import { ApplicationCard } from "../../src/components/ApplicationCard";
import { DocumentType } from "../../src/models/Document";
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
  it("with a completed application renders the component", () => {
    const claim = new MockBenefitsApplicationBuilder().completed().create();
    const { container } = render(<ApplicationCardWithAppLogic claim={claim} />);

    expect(container.firstChild).toMatchSnapshot();
  });

  it("with a completed application renders a view status button", () => {
    const claim = new MockBenefitsApplicationBuilder().completed().create();
    render(<ApplicationCardWithAppLogic claim={claim} />);

    const button = screen.getByRole("link", {
      name: /View status updates and details/,
    });
    expect(button).toBeInTheDocument();
  });

  it("in progress claims don't show EIN in the title section", () => {
    const claim = new MockBenefitsApplicationBuilder().submitted().create();
    render(
      <ApplicationCardWithAppLogic claim={claim} number={2} documents={[]} />
    );
    expect(
      screen.getByRole("heading", { name: "Application 2" })
    ).toBeInTheDocument();
  });

  it("shows a spinner while documents are loading", () => {
    const claim = new MockBenefitsApplicationBuilder().submitted().create();

    render(
      <ApplicationCardWithAppLogic
        addAppLogicMocks={(appLogic) => {
          appLogic.documents.isLoadingClaimDocuments = () => true;
        }}
        claim={claim}
        number={2}
        documents={[]}
      />
    );

    expect(
      screen.queryByRole("progressbar", {
        "aria-label": "Loading documents",
      })
    ).toBeInTheDocument();
  });

  it("does not show a spinner if there is a document load error", () => {
    const claim = new MockBenefitsApplicationBuilder().submitted().create();
    const appErrors = new AppErrorInfoCollection([
      new AppErrorInfo({
        name: "DocumentsLoadError",
        meta: {
          application_id: "mock_application_id",
        },
      }),
    ]);

    render(
      <ApplicationCardWithAppLogic
        addAppLogicMocks={(appLogic) => {
          appLogic.appErrors = appErrors;
        }}
        claim={claim}
        number={2}
        documents={[]}
      />
    );

    expect(
      screen.queryByRole("progressbar", {
        "aria-label": "Loading documents",
      })
    ).not.toBeInTheDocument();
  });

  it("does not show a spinner for completed applications", () => {
    const claim = new MockBenefitsApplicationBuilder().completed().create();
    render(
      <ApplicationCardWithAppLogic claim={claim} number={2} documents={[]} />
    );

    expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
  });

  it("can display legal notices", () => {
    const claim = new MockBenefitsApplicationBuilder().completed().create();
    render(
      <ApplicationCardWithAppLogic
        claim={claim}
        number={2}
        documents={[
          {
            application_id: "mock-claim-id",
            document_type: DocumentType.appealAcknowledgment,
          },
          {
            application_id: "mock-claim-id",
            document_type: DocumentType.approvalNotice,
            fineos_document_id: "mock-document-3",
          },
        ]}
      />
    );
    expect(
      screen.getByRole("link", { name: /View your notices/ })
    ).toBeInTheDocument();
  });

  it("doesn't display notices if application is submitted", () => {
    const claim = new MockBenefitsApplicationBuilder().submitted().create();
    render(
      <ApplicationCardWithAppLogic
        claim={claim}
        number={2}
        documents={[
          {
            application_id: "mock-claim-id",
            document_type: DocumentType.appealAcknowledgment,
            fineos_document_id: "mock-document-1",
          },
          {
            application_id: "mock-claim-id",
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
