import React, { useEffect } from "react";
import AppErrorInfo from "../../../models/AppErrorInfo";
import AppErrorInfoCollection from "../../../models/AppErrorInfoCollection";
import InputChoiceGroup from "../../../components/InputChoiceGroup";
import LeaveReason from "../../../models/LeaveReason";
import PropTypes from "prop-types";
import QuestionPage from "../../../components/QuestionPage";
import Spinner from "../../../components/Spinner";
import tracker from "../../../services/tracker";
import useFormState from "../../../hooks/useFormState";
import useFunctionalInputProps from "../../../hooks/useFunctionalInputProps";
import { useTranslation } from "react-i18next";

export const UploadType = {
  mass_id: "UPLOAD_MASS_ID",
  non_mass_id: "UPLOAD_ID",
  upload_medical_certification: "UPLOAD_MEDICAL_CERTIFICATION",
  upload_proof_of_birth: "UPLOAD_PROOF_OF_BIRTH",
  upload_proof_of_placement: "UPLOAD_PROOF_OF_PLACEMENT",
  upload_pregnancy_medical_certification:
    "UPLOAD_PREGNANCY_MEDICAL_CERTIFICATION",
  upload_caring_leave_certification: "UPLOAD_CARING_LEAVE_CERTIFICATION",
};

export const UploadDocsOptions = (props) => {
  const {
    appLogic,
    query: { absence_case_id },
  } = props;
  const {
    claims: { claimDetail, isLoadingClaimDetail, loadClaimDetail },
    portalFlow,
  } = appLogic;
  const { t } = useTranslation();
  const { formState, updateFields } = useFormState();
  const upload_docs_options = formState.upload_docs_options;

  useEffect(() => {
    loadClaimDetail(absence_case_id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [absence_case_id]);

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  const choices = claimDetail
    ? getInputChoices(claimDetail.absence_periods, upload_docs_options, t)
    : [];

  const hasClaimDetailLoadError = appLogic.appErrors.items.some(
    (error) => error.name === "ClaimDetailLoadError"
  );

  if (hasClaimDetailLoadError) return null;

  if (isLoadingClaimDetail || !claimDetail)
    return (
      <div className="margin-top-8 text-center">
        <Spinner
          aria-valuetext={t("pages.claimsStatus.loadingClaimDetailLabel")}
        />
      </div>
    );

  const handleSave = async () => {
    if (!upload_docs_options) {
      const appErrorInfo = new AppErrorInfo({
        field: "upload_docs_options",
        message: t("errors.applications.upload_docs_options.required"),
        type: "required",
      });

      appLogic.setAppErrors(new AppErrorInfoCollection([appErrorInfo]));

      tracker.trackEvent("ValidationError", {
        issueField: appErrorInfo.field,
        issueType: appErrorInfo.type,
      });

      return;
    }

    return await portalFlow.goToNextPage(
      {},
      { claim_id: claimDetail.application_id, additionalDoc: "true" },
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

UploadDocsOptions.propTypes = {
  appLogic: PropTypes.object.isRequired,
  query: PropTypes.shape({
    absence_case_id: PropTypes.string.isRequired,
  }),
};

export default UploadDocsOptions;

/**
 * Determine what choices to show based on the abence period's leave reason
 * @param  {Array.AbsencePeriod} absencePeriods array of claim detail's absence periods
 * @param  {string} currentValue current value of input
 * @param  {Function} t useTranslation function
 * @returns {Array} array of input choices { checked, label, value }
 */
const getInputChoices = (absencePeriods, currentValue, t) => {
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
      checked: currentValue === UploadType.upload_proof_of_birth,
      label: t("pages.claimsUploadDocsOptions.certLabel_bonding_newborn", {
        context: "bonding_newborn",
      }),
      value: UploadType.upload_proof_of_birth,
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
      checked: currentValue === UploadType.upload_proof_of_placement,
      label: t("pages.claimsUploadDocsOptions.certLabel_bonding_adopt_foster", {
        context: "bonding_adopt_foster",
      }),
      value: UploadType.upload_proof_of_placement,
    });
  }

  if (
    absencePeriods.some((absencePeriod) => {
      return absencePeriod.reason === LeaveReason.pregnancy;
    })
  ) {
    choices.push({
      checked:
        currentValue === UploadType.upload_pregnancy_medical_certification,
      label: t("pages.claimsUploadDocsOptions.certLabel_medical", {
        // TODO (CP-2660): change context for pregnancy
        context: "medical",
      }),
      value: UploadType.upload_pregnancy_medical_certification,
    });
  }

  if (
    absencePeriods.some((absencePeriod) => {
      return absencePeriod.reason === LeaveReason.medical;
    })
  ) {
    choices.push({
      checked: currentValue === UploadType.upload_medical_certification,
      label: t("pages.claimsUploadDocsOptions.certLabel_medical", {
        context: "medical",
      }),
      value: UploadType.upload_medical_certification,
    });
  }

  if (
    absencePeriods.some((absencePeriod) => {
      return absencePeriod.reason === LeaveReason.care;
    })
  ) {
    choices.push({
      checked: currentValue === UploadType.upload_caring_leave_certification,
      label: t("pages.claimsUploadDocsOptions.certLabel_care", {
        context: "care",
      }),
      value: UploadType.upload_caring_leave_certification,
    });
  }

  return choices;
};
