import ClaimDetail, { AbsencePeriod } from "../../../../src/models/ClaimDetail";
import UploadDocsOptions, {
  UploadType,
} from "../../../../src/pages/applications/upload/index";
import { act, render, screen } from "@testing-library/react";
import LeaveReason from "../../../../src/models/LeaveReason";
import React from "react";
import User from "../../../../src/models/User";
import { map } from "lodash";
import useAppLogic from "../../../../src/hooks/useAppLogic";
import userEvent from "@testing-library/user-event";

jest.mock("../../../../src/services/tracker");

const UploadDocsOptionsWithAppLogic = ({
  addAppLogicMocks = (appLogic) => {},
  ...props
}) => {
  const appLogic = useAppLogic();
  appLogic.auth.requireLogin = jest.fn();
  appLogic.users.requireUserConsentToDataAgreement = jest.fn();
  appLogic.users.requireUserRole = jest.fn();
  appLogic.users.user = new User({ consented_to_data_sharing: true });
  appLogic.claims.loadClaimDetail = jest.fn();
  appLogic.portalFlow.goToNextPage = jest.fn();

  addAppLogicMocks(appLogic);

  return <UploadDocsOptions appLogic={appLogic} {...props} />;
};

const addClaimDetail = (appLogic, claimDetail) => {
  appLogic.claims.claimDetail = claimDetail;
};

const absencePeriodScenarios = {
  bondingWithNewBorn: {
    absencePeriod: new AbsencePeriod({
      reason: LeaveReason.bonding,
      reason_qualifier_one: "Newborn",
    }),
    uploadType: UploadType.upload_proof_of_birth,
    labelText: "Proof of birth",
  },
  bondingWithFoster: {
    absencePeriod: new AbsencePeriod({
      reason: LeaveReason.bonding,
      reason_qualifier_one: "Foster Care",
    }),
    uploadType: UploadType.upload_proof_of_placement,
    labelText: "Proof of placement",
  },
  bondingWithAdoption: {
    absencePeriod: new AbsencePeriod({
      reason: LeaveReason.bonding,
      reason_qualifier_one: "Adoption",
    }),
    uploadType: UploadType.upload_proof_of_placement,
    labelText: "Proof of placement",
  },
  medical: {
    absencePeriod: new AbsencePeriod({ reason: LeaveReason.medical }),
    uploadType: UploadType.upload_medical_certification,
    labelText: "Certification of Your Serious Health Condition",
  },
  pregnancy: {
    absencePeriod: new AbsencePeriod({ reason: LeaveReason.pregnancy }),
    uploadType: UploadType.upload_pregnancy_medical_certification,
    labelText: "Certification of Your Serious Health Condition",
  },
  caring: {
    absencePeriod: new AbsencePeriod({ reason: LeaveReason.care }),
    uploadType: UploadType.upload_caring_leave_certification,
    labelText: "Certification of Your Family Member’s Serious Health Condition",
  },
};

describe("UploadDocsOptions", () => {
  it("renders the page and all input choices when claim has an absence period for each leave reason", () => {
    const claimDetail = new ClaimDetail({
      absence_periods: map(
        Object.values(absencePeriodScenarios),
        "absencePeriod"
      ),
      application_id: "mock-claim-id",
    });

    const { container } = render(
      <UploadDocsOptionsWithAppLogic
        addAppLogicMocks={(appLogic) => {
          addClaimDetail(appLogic, claimDetail);
        }}
        query={{
          absence_case_id: "mock-absence-id",
        }}
      />
    );

    expect(container.firstChild).toMatchSnapshot();
  });

  describe("when claim has no absence periods", () => {
    let appLogic, container;
    beforeEach(() => {
      const claimDetail = new ClaimDetail({
        absence_periods: [],
        application_id: "mock-claim-id",
      });

      ({ container } = render(
        <UploadDocsOptionsWithAppLogic
          addAppLogicMocks={(_appLogic) => {
            appLogic = _appLogic;
            addClaimDetail(_appLogic, claimDetail);
          }}
          query={{
            absence_case_id: "mock-absence-id",
          }}
        />
      ));
    });

    it("renders only id input choices", () => {
      expect(container.firstChild).toMatchSnapshot();
    });

    it(`routes to the page for ${UploadType.mass_id} when "Massachusetts driver’s license or ID" radio is clicked`, async () => {
      const radio = screen.getByLabelText(
        /Massachusetts driver’s license or ID/
      );

      await act(async () => {
        await userEvent.click(radio);
      });

      const submitButton = screen.getByRole("button", {
        name: "Save and continue",
      });

      await act(async () => {
        await userEvent.click(submitButton);
      });

      expect(appLogic.portalFlow.goToNextPage).toHaveBeenCalledWith(
        {},
        { claim_id: "mock-claim-id", additionalDoc: "true" },
        UploadType.mass_id
      );
    });

    it(`routes to the page for ${UploadType.non_mass_id} when "Different identification documentation" radio is clicked`, async () => {
      const radio = screen.getByLabelText(
        /Different identification documentation/
      );

      await act(async () => {
        await userEvent.click(radio);
      });

      const submitButton = screen.getByRole("button", {
        name: "Save and continue",
      });

      await act(async () => {
        await userEvent.click(submitButton);
      });

      expect(appLogic.portalFlow.goToNextPage).toHaveBeenCalledWith(
        {},
        { claim_id: "mock-claim-id", additionalDoc: "true" },
        UploadType.non_mass_id
      );
    });
  });

  it("shows a validation error when a user does not choose a doc type option", async () => {
    const claimDetail = new ClaimDetail({
      application_id: "mock-claim-id",
      absence_periods: [],
    });

    let appLogic;

    render(
      <UploadDocsOptionsWithAppLogic
        addAppLogicMocks={(_appLogic) => {
          appLogic = _appLogic;
          addClaimDetail(_appLogic, claimDetail);
        }}
        query={{
          absence_case_id: "mock-absence-id",
        }}
      />
    );

    const submitButton = screen.getByRole("button", {
      name: "Save and continue",
    });

    await act(async () => {
      await userEvent.click(submitButton);
    });

    const { field, type } = appLogic.appErrors.items[0];
    expect([field, type]).toEqual(["upload_docs_options", "required"]);
    expect(appLogic.portalFlow.goToNextPage).not.toHaveBeenCalled();
  });

  map(
    absencePeriodScenarios,
    ({ absencePeriod, uploadType, labelText }, key) => {
      describe(`when absence period is ${key}`, () => {
        let appLogic;

        beforeEach(() => {
          const claimDetail = new ClaimDetail({
            application_id: "mock-claim-id",
            absence_periods: [absencePeriod],
          });
          render(
            <UploadDocsOptionsWithAppLogic
              addAppLogicMocks={(_appLogic) => {
                appLogic = _appLogic;
                addClaimDetail(_appLogic, claimDetail);
              }}
              query={{
                absence_case_id: "mock-absence-id",
              }}
            />
          );
        });

        it(`renders radio with ${labelText}`, async () => {
          const radio = await screen.findByLabelText(labelText);

          expect(radio).toBeInTheDocument();
        });

        it(`routes to the page for ${uploadType} when radio is clicked`, async () => {
          const radio = screen.getByLabelText(labelText);

          await act(async () => {
            await userEvent.click(radio);
          });

          const submitButton = screen.getByRole("button", {
            name: "Save and continue",
          });

          await act(async () => {
            await userEvent.click(submitButton);
          });

          expect(appLogic.portalFlow.goToNextPage).toHaveBeenCalledWith(
            {},
            { claim_id: "mock-claim-id", additionalDoc: "true" },
            uploadType
          );
        });
      });
    }
  );
});
