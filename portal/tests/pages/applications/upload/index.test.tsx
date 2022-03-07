import UploadDocsOptions, {
  UploadType,
} from "../../../../src/pages/applications/upload/index";
import { act, screen, waitFor } from "@testing-library/react";
import { AbsencePeriod } from "../../../../src/models/AbsencePeriod";
import { AppLogic } from "../../../../src/hooks/useAppLogic";
import ClaimDetail from "../../../../src/models/ClaimDetail";
import LeaveReason from "../../../../src/models/LeaveReason";
import { renderPage } from "../../../test-utils";
import userEvent from "@testing-library/user-event";

jest.mock("../../../../src/services/tracker");

function setup(claimDetail: Partial<ClaimDetail> = {}) {
  const claim = new ClaimDetail({
    fineos_absence_id: "mock-absence-id",
    application_id: "mock-claim-id",
    ...claimDetail,
  });
  const goToNextPageSpy = jest.fn();
  const setErrorsSpy = jest.fn();

  const utils = renderPage(
    UploadDocsOptions,
    {
      addCustomSetup: (appLogic: AppLogic) => {
        appLogic.claims.claimDetail = claim;
        appLogic.claims.loadClaimDetail = jest.fn();
        appLogic.portalFlow.goToNextPage = goToNextPageSpy;
        appLogic.setErrors = setErrorsSpy;
      },
    },
    {
      query: { absence_id: claim.fineos_absence_id },
    }
  );

  return { ...utils, setErrorsSpy, goToNextPageSpy };
}

const absencePeriodScenarios = {
  bondingWithNewBorn: {
    absencePeriod: new AbsencePeriod({
      reason: LeaveReason.bonding,
      reason_qualifier_one: "Newborn",
    }),
    uploadType: UploadType.proof_of_birth,
    labelText: "Proof of birth",
  },
  bondingWithFoster: {
    absencePeriod: new AbsencePeriod({
      reason: LeaveReason.bonding,
      reason_qualifier_one: "Foster Care",
    }),
    uploadType: UploadType.proof_of_placement,
    labelText: "Proof of placement",
  },
  bondingWithAdoption: {
    absencePeriod: new AbsencePeriod({
      reason: LeaveReason.bonding,
      reason_qualifier_one: "Adoption",
    }),
    uploadType: UploadType.proof_of_placement,
    labelText: "Proof of placement",
  },
  medical: {
    absencePeriod: new AbsencePeriod({ reason: LeaveReason.medical }),
    uploadType: UploadType.medical_certification,
    labelText: "Certification of Your Serious Health Condition",
  },
  pregnancy: {
    absencePeriod: new AbsencePeriod({ reason: LeaveReason.pregnancy }),
    uploadType: UploadType.pregnancy_medical_certification,
    labelText: "Certification of Your Serious Health Condition",
  },
  caring: {
    absencePeriod: new AbsencePeriod({ reason: LeaveReason.care }),
    uploadType: UploadType.caring_leave_certification,
    labelText: "Certification of Your Family Member’s Serious Health Condition",
  },
};

describe("UploadDocsOptions", () => {
  it("renders the page and all input choices when claim has an absence period for each leave reason", () => {
    const { container } = setup({
      absence_periods: Object.values(absencePeriodScenarios).map(
        (scenario) => scenario.absencePeriod
      ),
    });

    expect(container.firstChild).toMatchSnapshot();
  });

  describe("when claim has no absence periods", () => {
    it("renders only id input choices", () => {
      const { container } = setup({ absence_periods: [] });

      expect(container.firstChild).toMatchSnapshot();
    });

    it(`routes to the page for ${UploadType.mass_id} when "Massachusetts driver’s license or ID" radio is clicked`, async () => {
      const { goToNextPageSpy } = setup({ absence_periods: [] });

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

      expect(goToNextPageSpy).toHaveBeenCalledWith(
        {},
        { claim_id: "mock-claim-id", absence_id: "mock-absence-id" },
        UploadType.mass_id
      );
    });

    it(`routes to the page for ${UploadType.non_mass_id} when "Different identification documentation" radio is clicked`, async () => {
      const { goToNextPageSpy } = setup({ absence_periods: [] });

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

      expect(goToNextPageSpy).toHaveBeenCalledWith(
        {},
        { claim_id: "mock-claim-id", absence_id: "mock-absence-id" },
        UploadType.non_mass_id
      );
    });
  });

  it("shows a validation error when a user does not choose a doc type option", async () => {
    const { goToNextPageSpy, setErrorsSpy } = setup();

    const submitButton = screen.getByRole("button", {
      name: "Save and continue",
    });

    userEvent.click(submitButton);

    await waitFor(() => {
      expect(setErrorsSpy.mock.calls[0][0][0].issues).toEqual([
        {
          field: "upload_docs_options",
          type: "required",
          namespace: "applications",
        },
      ]);
    });

    expect(goToNextPageSpy).not.toHaveBeenCalled();
  });

  Object.entries(absencePeriodScenarios).forEach(
    ([key, { absencePeriod, uploadType, labelText }]) => {
      describe(`when absence period is ${key}`, () => {
        it(`renders radio with ${labelText}`, async () => {
          setup({
            absence_periods: [absencePeriod],
          });
          const radio = await screen.findByLabelText(labelText);

          expect(radio).toBeInTheDocument();
        });

        it(`routes to the page for ${uploadType} when radio is clicked`, async () => {
          const { goToNextPageSpy } = setup({
            absence_periods: [absencePeriod],
          });

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

          expect(goToNextPageSpy).toHaveBeenCalledWith(
            {},
            { claim_id: "mock-claim-id", absence_id: "mock-absence-id" },
            uploadType
          );
        });
      });
    }
  );
});
