import { act, render, screen } from "@testing-library/react";

import AppErrorInfo from "../../src/models/AppErrorInfo";
import AppErrorInfoCollection from "../../src/models/AppErrorInfoCollection";
import { ApplicationCard } from "../../src/components/ApplicationCard";
import ClaimDetail from "../../src/models/ClaimDetail";
import { DocumentType } from "../../src/models/Document";

import { MockBenefitsApplicationBuilder } from "../test-utils";
import React from "react";
import User from "../../src/models/User";
import { merge } from "lodash";
import useAppLogic from "../../src/hooks/useAppLogic";
import userEvent from "@testing-library/user-event";

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

    const button = screen.getByRole("button", {
      name: /View status updates and details/,
    });
    expect(button).toBeInTheDocument();
  });

  // Functionality removed in a hotfix
  // eslint-disable-next-line jest/no-disabled-tests
  it.skip("with a completed application when the user clicks the view status button disables the button", async () => {
    let appLogic;
    const claim = new MockBenefitsApplicationBuilder().completed().create();
    render(
      <ApplicationCardWithAppLogic
        addAppLogicMocks={(_appLogic) => {
          appLogic = _appLogic;
          appLogic.claims.isLoadingClaimDetail = true;
          appLogic.claims.loadClaimDetail = jest.fn(
            () => new Promise((resolve, reject) => {})
          );
        }}
        claim={claim}
      />
    );

    const button = screen.getByRole("button", {
      name: /View status updates and details/,
    });
    expect(button).toBeEnabled();
    await act(async () => {
      await userEvent.click(button);
    });
    expect(button).toBeDisabled();
  });

  // Functionality removed in a hotfix
  // eslint-disable-next-line jest/no-disabled-tests
  it.skip("with a completed application when the user clicks the view status button loads claim details", async () => {
    let appLogic;
    const claim = new MockBenefitsApplicationBuilder().completed().create();
    render(
      <ApplicationCardWithAppLogic
        addAppLogicMocks={(_appLogic) => {
          appLogic = _appLogic;
          appLogic.claims.loadClaimDetail = jest.fn(
            () => new Promise((resolve, reject) => {})
          );
        }}
        claim={claim}
      />
    );

    const button = screen.getByRole("button", {
      name: /View status updates and details/,
    });
    await act(async () => {
      await userEvent.click(button);
    });
    expect(appLogic.claims.loadClaimDetail).toHaveBeenCalled();
  });

  it("with a completed application when the claim has loaded successfully, buttons redirect the user to the correct claim status link", async () => {
    let appLogic;
    const claim = new MockBenefitsApplicationBuilder().completed().create();
    render(
      <ApplicationCardWithAppLogic
        addAppLogicMocks={(_appLogic) => {
          appLogic = _appLogic;
          appLogic.claims.loadClaimDetail = jest.fn(() =>
            Promise.resolve(
              new ClaimDetail({
                fineos_absence_id: claim.fineos_absence_id,
              })
            )
          );
          appLogic.portalFlow.goTo = jest.fn();
        }}
        claim={claim}
      />
    );

    const expectButtonToRedirect = async (name, hash = "") => {
      const button = screen.getByRole("button", { name });
      await act(async () => {
        await userEvent.click(button);
      });

      expect(appLogic.portalFlow.goTo).toHaveBeenCalledWith(
        `/applications/status${hash ? "/" : ""}?absence_id=${
          claim.fineos_absence_id
        }${hash}`
      );
      jest.clearAllMocks();
    };

    await expectButtonToRedirect(/View status updates and details/);
    await expectButtonToRedirect(/View your notices/, "/#view_notices");
    await expectButtonToRedirect(
      /Respond to a request for information/,
      "/#upload_documents"
    );
  });

  // Functionality removed in a hotfix
  // eslint-disable-next-line jest/no-disabled-tests
  it.skip("with a completed application when the claim has failed the navigation buttons do not go to the next page", async () => {
    let appLogic;
    const claim = new MockBenefitsApplicationBuilder().completed().create();
    render(
      <ApplicationCardWithAppLogic
        addAppLogicMocks={(_appLogic) => {
          appLogic = _appLogic;
          appLogic.claims.loadClaimDetail = jest.fn(
            () =>
              new Promise((resolve, reject) => {
                resolve();
              })
          );
          appLogic.portalFlow.goTo = jest.fn();
        }}
        claim={claim}
      />
    );

    const expectButtonNotToRedirect = async (name) => {
      const button = screen.getByRole("button", { name });
      await act(async () => {
        await userEvent.click(button);
      });

      expect(appLogic.portalFlow.goTo).not.toHaveBeenCalled();
      jest.clearAllMocks();
    };

    await expectButtonNotToRedirect(/View status updates and details/);
    await expectButtonNotToRedirect(/View your notices/);
    await expectButtonNotToRedirect(/Respond to a request for information/);
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
        claim={claim}
        number={2}
        documents={[]}
        isLoadingDocuments
      />
    );

    expect(
      screen.queryByRole("progressbar", {
        "aria-valuetext": "Loading documents",
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
        isLoadingDocuments
      />
    );

    expect(
      screen.queryByRole("progressbar", {
        "aria-valuetext": "Loading documents",
      })
    ).not.toBeInTheDocument();
  });

  it("does not show a spinner for completed applications", () => {
    const claim = new MockBenefitsApplicationBuilder().completed().create();

    render(
      <ApplicationCardWithAppLogic
        claim={claim}
        number={2}
        documents={[]}
        isLoadingDocuments
      />
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
      screen.getByRole("button", { name: /View your notices/ })
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
