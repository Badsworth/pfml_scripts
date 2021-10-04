import BenefitsApplication, {
  ReasonQualifier,
} from "../../models/BenefitsApplication";
import AppErrorInfo from "../../models/AppErrorInfo";
import AppErrorInfoCollection from "../../models/AppErrorInfoCollection";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import LeaveReason from "../../models/LeaveReason";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { get } from "lodash";
import tracker from "../../services/tracker";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "react-i18next";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

export const UploadType = {
  mass_id: "UPLOAD_MASS_ID",
  non_mass_id: "UPLOAD_ID",
  certification: "UPLOAD_CERTIFICATION",
};

export const UploadDocsOptions = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();
  const { formState, updateFields } = useFormState();
  const upload_docs_options = formState.upload_docs_options;

  const leaveReason = get(claim, "leave_details.reason");
  const reasonQualifier = get(claim, "leave_details.reason_qualifier");
  const contentContext = {
    [LeaveReason.bonding]: {
      [ReasonQualifier.newBorn]: "bonding_newborn",
      [ReasonQualifier.adoption]: "bonding_adopt_foster",
      [ReasonQualifier.fosterCare]: "bonding_adopt_foster",
    },
    [LeaveReason.medical]: "medical",
    [LeaveReason.pregnancy]: "medical",
    [LeaveReason.care]: "care",
  };
  const certChoiceLabel =
    leaveReason === LeaveReason.bonding
      ? contentContext[leaveReason][reasonQualifier]
      : contentContext[leaveReason];

  const handleSave = () => {
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

    const showStateId =
      upload_docs_options === UploadType.certification
        ? undefined
        : upload_docs_options === UploadType.mass_id;
    return appLogic.portalFlow.goToNextPage(
      { claim },
      { claim_id: claim.application_id, showStateId, additionalDoc: "true" },
      upload_docs_options
    );
  };

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  return (
    <QuestionPage
      title={t("pages.claimsUploadDocsOptions.title")}
      onSave={handleSave}
    >
      <InputChoiceGroup
        {...getFunctionalInputProps("upload_docs_options")}
        choices={[
          {
            checked: upload_docs_options === UploadType.mass_id,
            label: t("pages.claimsUploadDocsOptions.stateIdLabel"),
            value: UploadType.mass_id,
          },
          {
            checked: upload_docs_options === UploadType.non_mass_id,
            label: t("pages.claimsUploadDocsOptions.nonStateIdLabel"),
            value: UploadType.non_mass_id,
          },
          {
            checked: upload_docs_options === UploadType.certification,
            label: t("pages.claimsUploadDocsOptions.certLabel", {
              context: certChoiceLabel,
            }),
            value: UploadType.certification,
          },
        ]}
        label={t("pages.claimsUploadDocsOptions.sectionLabel")}
        hint={t("pages.claimsUploadDocsOptions.sectionHint")}
        type="radio"
      />
    </QuestionPage>
  );
};

UploadDocsOptions.propTypes = {
  claim: PropTypes.instanceOf(BenefitsApplication),
  appLogic: PropTypes.object.isRequired,
};

export default withBenefitsApplication(UploadDocsOptions);
