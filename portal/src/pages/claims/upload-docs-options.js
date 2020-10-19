import Claim, { LeaveReason, ReasonQualifier } from "../../models/Claim";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { get } from "lodash";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "react-i18next";
import withClaim from "../../hoc/withClaim";

export const UploadType = {
  mass_id: "UPLOAD_MASS_ID",
  non_mass_id: "UPLOAD_ID",
  certification: "UPLOAD_CERTIFICATION",
};

export const UploadDocsOptions = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();
  const { formState, updateFields } = useFormState();
  const nextPage = formState.nextPage;

  const leaveReason = get(claim, "leave_details.reason");
  const reasonQualifier = get(claim, "leave_details.reason_qualifier");
  const contentContext = {
    [LeaveReason.bonding]: {
      [ReasonQualifier.newBorn]: "bonding_newborn",
      [ReasonQualifier.adoption]: "bonding_adopt_foster",
      [ReasonQualifier.fosterCare]: "bonding_adopt_foster",
    },
    [LeaveReason.medical]: "medical",
  };
  let certChoiceLabel;
  switch (leaveReason) {
    case LeaveReason.medical:
      certChoiceLabel = contentContext[leaveReason];
      break;
    case LeaveReason.bonding:
      certChoiceLabel = contentContext[leaveReason][reasonQualifier];
      break;
  }

  const handleSave = () => {
    if (nextPage === UploadType.certification) {
      return appLogic.portalFlow.goToNextPage(
        { claim },
        { claim_id: claim.application_id },
        nextPage
      );
    } else {
      const showStateId = nextPage === UploadType.mass_id;
      return appLogic.portalFlow.goToNextPage(
        { claim },
        { claim_id: claim.application_id, showStateId },
        nextPage
      );
    }
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
        {...getFunctionalInputProps("nextPage")}
        choices={[
          {
            checked: nextPage === UploadType.mass_id,
            label: t("pages.claimsUploadDocsOptions.stateIdLabel"),
            value: UploadType.mass_id,
          },
          {
            checked: nextPage === UploadType.non_mass_id,
            label: t("pages.claimsUploadDocsOptions.nonStateIdLabel"),
            value: UploadType.non_mass_id,
          },
          {
            checked: nextPage === UploadType.certification,
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
  claim: PropTypes.instanceOf(Claim),
  appLogic: PropTypes.object.isRequired,
};

export default withClaim(UploadDocsOptions);
