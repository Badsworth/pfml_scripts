import AppErrorInfo from "../../models/AppErrorInfo";
import AppErrorInfoCollection from "../../models/AppErrorInfoCollection";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import tracker from "../../services/tracker";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "react-i18next";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

const UploadType = {
  STATE_ID: "UPLOAD_STATE_ID",
  OTHER_ID: "UPLOAD_OTHER_ID",
  PROOF_OF_BIRTH: "UPLOAD_PROOF_OF_BIRTH",
  ADOPTION_STATEMENT: "UPLOAD_ADOPTION_STATEMENT",
  MEDICAL_CERTIFICATION: "UPLOAD_MEDICAL_CERTIFICATION",
  PREGNANCY_CERTIFICATION: "UPLOAD_PREGNANCY_CERTIFICATION",
  CARING_CERTIFICATION: "UPLOADING_CARING_CERTIFICATION",
};

export const UploadDocsOptions = (props) => {
  const { appLogic, query } = props;
  const { t } = useTranslation();
  const { formState, updateFields } = useFormState();
  const upload_docs_options = formState.upload_docs_options;

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

    return appLogic.portalFlow.goToNextPage(
      {},
      { claim_id: query.claim_id, additionalDoc: "true" },
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
            checked: upload_docs_options === UploadType.STATE_ID,
            label: t("pages.claimsUploadDocsOptions.stateIdLabel"),
            value: UploadType.STATE_ID,
          },
          {
            checked: upload_docs_options === UploadType.OTHER_ID,
            label: t("pages.claimsUploadDocsOptions.nonStateIdLabel"),
            value: UploadType.OTHER_ID,
          },
          {
            checked: upload_docs_options === UploadType.MEDICAL_CERTIFICATION,
            label: t("pages.claimsUploadDocsOptions.certLabel", {
              context: "bonding_newborn",
            }),
            value: UploadType.MEDICAL_CERTIFICATION,
          },
          {
            checked: upload_docs_options === UploadType.PREGNANCY_CERTIFICATION,
            label: t("pages.claimsUploadDocsOptions.certLabel", {
              context: "bonding_newborn",
            }),
            value: UploadType.PREGNANCY_CERTIFICATION,
          },
          {
            checked: upload_docs_options === UploadType.PROOF_OF_BIRTH,
            label: t("pages.claimsUploadDocsOptions.certLabel", {
              context: "bonding_newborn",
            }),
            value: UploadType.PROOF_OF_BIRTH,
          },
          {
            checked: upload_docs_options === UploadType.ADOPTION_STATEMENT,
            label: t("pages.claimsUploadDocsOptions.certLabel", {
              context: "bonding_adopt_foster",
            }),
            value: UploadType.ADOPTION_STATEMENT,
          },
          {
            checked: upload_docs_options === UploadType.CARING_CERTIFICATION,
            label: t("pages.claimsUploadDocsOptions.certLabel", {
              context: "care",
            }),
            value: UploadType.CARING_CERTIFICATION,
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
  appLogic: PropTypes.object.isRequired,
  query: PropTypes.shapeOf({
    claim_id: PropTypes.string.isRequired,
  }),
};

export default withBenefitsApplication(UploadDocsOptions);
