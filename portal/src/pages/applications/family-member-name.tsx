import { get, pick } from "lodash";
import withBenefitsApplication, {
  WithBenefitsApplicationProps,
} from "../../hoc/withBenefitsApplication";
import { CaringLeaveMetadata } from "../../models/BenefitsApplication";
import Fieldset from "../../components/core/Fieldset";
import FormLabel from "../../components/core/FormLabel";
import InputText from "../../components/core/InputText";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";

const caringLeavePath = "leave_details.caring_leave_metadata";

export const fields = [
  `claim.${caringLeavePath}.family_member_first_name`,
  `claim.${caringLeavePath}.family_member_middle_name`,
  `claim.${caringLeavePath}.family_member_last_name`,
];

export const FamilyMemberName = (props: WithBenefitsApplicationProps) => {
  const { t } = useTranslation();
  const { appLogic, claim } = props;

  const initialCaringLeaveMetadata = new CaringLeaveMetadata(
    get(claim, caringLeavePath)
  );

  const { formState, updateFields } = useFormState({
    leave_details: { caring_leave_metadata: initialCaringLeaveMetadata },
  });

  const handleSave = () =>
    // only send fields for this page
    appLogic.benefitsApplications.update(
      claim.application_id,
      pick({ claim: formState }, fields).claim || {}
    );

  const getFunctionalInputProps = useFunctionalInputProps({
    errors: appLogic.errors,
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

export default withBenefitsApplication(FamilyMemberName);
