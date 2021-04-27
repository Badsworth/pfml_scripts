import BenefitsApplication, {
  CaringLeaveMetadata,
} from "../../models/BenefitsApplication";
import { get, pick } from "lodash";
import InputDate from "../../components/InputDate";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

const caringLeaveMetadataKey = "leave_details.caring_leave_metadata";
export const fields = [
  `claim.${caringLeaveMetadataKey}.family_member_date_of_birth`,
];

export const FamilyMemberDateOfBirth = (props) => {
  const { t } = useTranslation();
  const { appLogic, claim } = props;

  // Make sure we always send a CaringLeaveMetadata object, even if all of the
  // fields are null. This is because the API needs to create a CaringLeaveMetadata
  // field on the application before it will validate any CaringLeaveMetadata
  // properties; without this it would be possible for a claimant to skip this page by just
  // clicking "Save and continue" instead of entering a date.
  const initialClaimState = pick(props.claim, caringLeaveMetadataKey);
  const { formState, updateFields } = useFormState({
    leave_details: {
      caring_leave_metadata: new CaringLeaveMetadata(
        get(initialClaimState, caringLeaveMetadataKey)
      ),
    },
  });

  const handleSave = async () => {
    await appLogic.benefitsApplications.update(claim.application_id, formState);
  };

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  return (
    <QuestionPage
      title={t("pages.claimsLeaveReason.title")}
      onSave={handleSave}
    >
      <InputDate
        {...getFunctionalInputProps(
          "leave_details.caring_leave_metadata.family_member_date_of_birth"
        )}
        label={t("pages.claimsFamilyMemberDateOfBirth.sectionLabel")}
        example={t("components.form.dateInputExample")}
        dayLabel={t("components.form.dateInputDayLabel")}
        monthLabel={t("components.form.dateInputMonthLabel")}
        yearLabel={t("components.form.dateInputYearLabel")}
      />
    </QuestionPage>
  );
};

FamilyMemberDateOfBirth.propTypes = {
  appLogic: PropTypes.object.isRequired,
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
  query: PropTypes.object.isRequired,
};

export default withBenefitsApplication(FamilyMemberDateOfBirth);
