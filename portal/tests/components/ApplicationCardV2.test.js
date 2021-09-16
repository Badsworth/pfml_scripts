import { act, render, screen } from "@testing-library/react";

import { ApplicationCardV2 } from "../../src/components/ApplicationCardV2";
import ClaimDetail from "../../src/models/ClaimDetail";
import { MockBenefitsApplicationBuilder } from "../test-utils";
import React from "react";
import User from "../../src/models/User";
import useAppLogic from "../../src/hooks/useAppLogic";
import userEvent from "@testing-library/user-event";

const ApplicationCardV2WithAppLogic = ({
  // eslint-disable-next-line react/prop-types
  addAppLogicMocks = (appLogic) => {},
  ...props
}) => {
  const appLogic = useAppLogic();
  appLogic.auth.requireLogin = jest.fn();
  appLogic.users.requireUserConsentToDataAgreement = jest.fn();
  appLogic.users.requireUserRole = jest.fn();
  appLogic.users.user = new User({ consented_to_data_sharing: true });

  appLogic.documents.loadAll = jest.fn();

  addAppLogicMocks(appLogic);

  return <ApplicationCardV2 appLogic={appLogic} {...props} />;
};

describe("ApplicationCardV2", () => {
  it("with a completed application renders the component", () => {
    const claim = new MockBenefitsApplicationBuilder().completed().create();
    const { container } = render(
      <ApplicationCardV2WithAppLogic claim={claim} />
    );

    expect(container.firstChild).toMatchSnapshot();
  });

  it("with a completed application renders a view status button", () => {
    const claim = new MockBenefitsApplicationBuilder().completed().create();
    render(<ApplicationCardV2WithAppLogic claim={claim} />);

    const button = screen.getByRole("button");
    expect(button).toHaveTextContent("View status updates and details");
  });

  it("with a completed application when the user clicks the view status button disables the button", async () => {
    let appLogic;
    const claim = new MockBenefitsApplicationBuilder().completed().create();
    render(
      <ApplicationCardV2WithAppLogic
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

    const button = screen.getByRole("button");
    expect(button).not.toHaveAttribute("disabled");
    await act(async () => {
      await userEvent.click(button);
    });
    expect(button).toHaveAttribute("disabled");
  });

  it("with a completed application when the user clicks the view status button loads claim details", async () => {
    let appLogic;
    const claim = new MockBenefitsApplicationBuilder().completed().create();
    render(
      <ApplicationCardV2WithAppLogic
        addAppLogicMocks={(_appLogic) => {
          appLogic = _appLogic;
          appLogic.claims.loadClaimDetail = jest.fn(
            () => new Promise((resolve, reject) => {})
          );
        }}
        claim={claim}
      />
    );

    const button = screen.getByRole("button");
    await act(async () => {
      await userEvent.click(button);
    });
    expect(appLogic.claims.loadClaimDetail).toHaveBeenCalled();
  });

  it("with a completed application when the claim has loaded successfully redirects the user to the claim status page", async () => {
    let appLogic;
    const claim = new MockBenefitsApplicationBuilder().completed().create();
    render(
      <ApplicationCardV2WithAppLogic
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

    const button = screen.getByRole("button");
    await act(async () => {
      await userEvent.click(button);
    });
    expect(appLogic.portalFlow.goTo).toHaveBeenCalledWith(
      `/applications/status?absence_case_id=${claim.fineos_absence_id}`
    );
  });

  it("with a completed application when the claim has failed to be loaded renders a view status button", async () => {
    let appLogic;
    const claim = new MockBenefitsApplicationBuilder().completed().create();
    render(
      <ApplicationCardV2WithAppLogic
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

    const button = screen.getByRole("button");
    await act(async () => {
      await userEvent.click(button);
    });
    expect(appLogic.portalFlow.goTo).not.toHaveBeenCalled();
  });
});
