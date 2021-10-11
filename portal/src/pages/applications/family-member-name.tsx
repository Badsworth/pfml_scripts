import BenefitsApplication, {
  CaringLeaveMetadata,
} from "../../models/BenefitsApplication";
import { get, pick } from "lodash";
import Fieldset from "../../components/Fieldset";
import FormLabel from "../../components/FormLabel";
import InputText from "../../components/InputText";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

const caringLeavePath = "leave_details.caring_leave_metadata";

export const fields = [
  `claim.${caringLeavePath}.family_member_first_name`,
  `claim.${caringLeavePath}.family_member_middle_name`,
  `claim.${caringLeavePath}.family_member_last_name`,
];

export const FamilyMemberName = (props) => {
  const { t } = useTranslation();
  const { appLogic, claim } = props;

  const initialCaringLeaveMetadata = new CaringLeaveMetadata(
    get(claim, caringLeavePath)
  );
  // @ts-expect-error ts-migrate(2339) FIXME: Property 'formState' does not exist on type 'FormS... Remove this comment to see the full error message
  const { formState, updateFields } = useFormState({
    leave_details: { caring_leave_metadata: initialCaringLeaveMetadata },
  });

  const handleSave = () =>
    // only send fields for this page
    appLogic.benefitsApplications.update(
      claim.application_id,
      pick({ claim: formState }, fields).claim
    );

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
      <Fieldset>
        <FormLabel
          component="legend"
          hint={t("pages.claimsFamilyMemberName.sectionHint")}
        >
          {t("pages.claimsFamilyMemberName.sectionLabel")}
        </FormLabel>
        <InputText
          {...getFunctionalInputProps(
            `${caringLeavePath}.family_member_first_name`
          )}
          label={t("pages.claimsFamilyMemberName.firstNameLabel")}
          smallLabel
        />
        <InputText
          {...getFunctionalInputProps(
            `${caringLeavePath}.family_member_middle_name`
          )}
          label={t("pages.claimsFamilyMemberName.middleNameLabel")}
          optionalText={t("components.form.optional")}
          smallLabel
        />
        <InputText
          {...getFunctionalInputProps(
            `${caringLeavePath}.family_member_last_name`
          )}
          label={t("pages.claimsFamilyMemberName.lastNameLabel")}
          smallLabel
        />
      </Fieldset>
    </QuestionPage>
  );
};

FamilyMemberName.propTypes = {
  appLogic: PropTypes.object.isRequired,
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
};

export default withBenefitsApplication(FamilyMemberName);
