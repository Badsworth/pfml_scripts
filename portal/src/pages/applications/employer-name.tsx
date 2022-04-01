import withBenefitsApplication, {
  WithBenefitsApplicationProps,
} from "../../hoc/withBenefitsApplication";
import Fieldset from "src/components/core/Fieldset";
import FormLabel from "src/components/core/FormLabel";
import InputText from "../../components/core/InputText";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { pick } from "lodash";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";

export const fields = ["claim.additional_user_not_found_info.employer_name"];

export const EmployerName = (props: WithBenefitsApplicationProps) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState(
    pick(props, ["claim.additional_user_not_found_info"]).claim
  );

  const handleSave = () =>
    appLogic.benefitsApplications.update(claim.application_id, formState);

  const getFunctionalInputProps = useFunctionalInputProps({
    errors: appLogic.errors,
    formState,
    updateFields,
  });

  return (
    <QuestionPage
      title={t("pages.claimsEmploymentStatus.title")}
      onSave={handleSave}
    >
      <Fieldset>
        <FormLabel component="legend">
          {t("pages.claimsAdditionalUserNotFoundInfo.employerNameTitle")}
        </FormLabel>
        <InputText
          {...getFunctionalInputProps(
            "additional_user_not_found_info.employer_name"
          )}
          label={t("pages.claimsAdditionalUserNotFoundInfo.employerNameLabel")}
          hint=""
          smallLabel={true}
        />
      </Fieldset>
    </QuestionPage>
  );
};

export default withBenefitsApplication(EmployerName);
