import React, { useEffect } from "react";
import { TFunction, useTranslation } from "react-i18next";
import { AbsencePeriod } from "../../../models/AbsencePeriod";
import { AppLogic } from "../../../hooks/useAppLogic";
import BackButton from "../../../components/BackButton";
import ErrorInfo from "../../../models/ErrorInfo";
import InputChoiceGroup from "../../../components/core/InputChoiceGroup";
import LeaveReason from "../../../models/LeaveReason";
import QuestionPage from "../../../components/QuestionPage";
import Spinner from "../../../components/core/Spinner";
import tracker from "../../../services/tracker";
import useFormState from "../../../hooks/useFormState";
import useFunctionalInputProps from "../../../hooks/useFunctionalInputProps";

export const UploadType = {
  mass_id: "UPLOAD_MASS_ID",
  non_mass_id: "UPLOAD_ID",
  medical_certification: "UPLOAD_MEDICAL_CERTIFICATION",
  proof_of_birth: "UPLOAD_PROOF_OF_BIRTH",
  proof_of_placement: "UPLOAD_PROOF_OF_PLACEMENT",
  pregnancy_medical_certification: "UPLOAD_PREGNANCY_MEDICAL_CERTIFICATION",
  caring_leave_certification: "UPLOAD_CARING_LEAVE_CERTIFICATION",
};

interface Props {
  appLogic: AppLogic;
  query: {
    absence_id: string;
  };
}

export const UploadDocsOptions = (props: Props) => {
  const {
    appLogic,
    query: { absence_id },
  } = props;
  const {
    claims: { claimDetail, isLoadingClaimDetail, loadClaimDetail },
    portalFlow,
  } = appLogic;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState();
  const upload_docs_options = formState.upload_docs_options;

  useEffect(() => {
    loadClaimDetail(absence_id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [absence_id]);

  const getFunctionalInputProps = useFunctionalInputProps({
    errors: appLogic.errors,
    formState,
    updateFields,
  });

  const choices = claimDetail
    ? getInputChoices(claimDetail.absence_periods, upload_docs_options, t)
    : [];

  // we should still display content if there are exclusively DocumentsLoadErrors.
  const hasNonDocumentsLoadError = appLogic.errors.some(
    (error) => error.name !== "DocumentsLoadError"
  );
  if (hasNonDocumentsLoadError) {
    return <BackButton />;
  }

  if (isLoadingClaimDetail || !claimDetail)
    return (
      <div className="margin-top-8 text-center">
        <Spinner aria-label={t("pages.claimsStatus.loadingClaimDetailLabel")} />
      </div>
    );

  const handleSave = async () => {
    if (!upload_docs_options) {
      const errorInfo = new ErrorInfo({
        field: "upload_docs_options",
        message: t("errors.applications.upload_docs_options.required"),
        type: "required",
      });

      appLogic.setErrors([errorInfo]);

      tracker.trackEvent("ValidationError", {
        issueField: errorInfo.field || "",
        issueType: errorInfo.type || "",
      });

      return;
    }

    return await portalFlow.goToNextPage(
      {},
      {
        claim_id: claimDetail.application_id,
        absence_id: claimDetail.fineos_absence_id,
      },
      upload_docs_options
    );
  };

  return (
    <QuestionPage
      title={t("pages.claimsUploadDocsOptions.title")}
      onSave={handleSave}
    >
      <InputChoiceGroup
        {...getFunctionalInputProps("upload_docs_options")}
        choices={choices}
        label={t("pages.claimsUploadDocsOptions.sectionLabel")}
        hint={t("pages.claimsUploadDocsOptions.sectionHint")}
        type="radio"
      />
    </QuestionPage>
  );
};

export default UploadDocsOptions;

/**
 * Determine what choices to show based on the absence period's leave reason
 */
const getInputChoices = (
  absencePeriods: AbsencePeriod[],
  currentValue: string,
  t: TFunction
) => {
  const choices = [
    {
      checked: currentValue === UploadType.mass_id,
      label: t("pages.claimsUploadDocsOptions.stateIdLabel"),
      value: UploadType.mass_id,
    },
    {
      checked: currentValue === UploadType.non_mass_id,
      label: t("pages.claimsUploadDocsOptions.nonStateIdLabel"),
      value: UploadType.non_mass_id,
    },
  ];

  if (
    absencePeriods.some((absencePeriod) => {
      return (
        absencePeriod.reason === LeaveReason.bonding &&
        absencePeriod.reason_qualifier_one === "Newborn"
      );
    })
  ) {
    choices.push({
      checked: currentValue === UploadType.proof_of_birth,
      label: t("pages.claimsUploadDocsOptions.certLabel_bonding_newborn", {
        context: "bonding_newborn",
      }),
      value: UploadType.proof_of_birth,
    });
  }

  if (
    absencePeriods.some((absencePeriod) => {
      return (
        absencePeriod.reason === LeaveReason.bonding &&
        (absencePeriod.reason_qualifier_one === "Adoption" ||
          absencePeriod.reason_qualifier_one === "Foster Care")
      );
    })
  ) {
    choices.push({
      checked: currentValue === UploadType.proof_of_placement,
      label: t("pages.claimsUploadDocsOptions.certLabel_bonding_adopt_foster", {
        context: "bonding_adopt_foster",
      }),
      value: UploadType.proof_of_placement,
    });
  }

  if (
    absencePeriods.some((absencePeriod) => {
      return absencePeriod.reason === LeaveReason.pregnancy;
    })
  ) {
    choices.push({
      checked: currentValue === UploadType.pregnancy_medical_certification,
      label: t("pages.claimsUploadDocsOptions.certLabel_medical", {
        // TODO (CP-2660): change context for pregnancy
        context: "medical",
      }),
      value: UploadType.pregnancy_medical_certification,
    });
  }

  if (
    absencePeriods.some((absencePeriod) => {
      return absencePeriod.reason === LeaveReason.medical;
    })
  ) {
    choices.push({
      checked: currentValue === UploadType.medical_certification,
      label: t("pages.claimsUploadDocsOptions.certLabel_medical", {
        context: "medical",
      }),
      value: UploadType.medical_certification,
    });
  }

  if (
    absencePeriods.some((absencePeriod) => {
      return absencePeriod.reason === LeaveReason.care;
    })
  ) {
    choices.push({
      checked: currentValue === UploadType.caring_leave_certification,
      label: t("pages.claimsUploadDocsOptions.certLabel_care", {
        context: "care",
      }),
      value: UploadType.caring_leave_certification,
    });
  }

  return choices;
};
