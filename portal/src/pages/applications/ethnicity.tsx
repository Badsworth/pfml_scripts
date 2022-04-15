import withBenefitsApplication, {
  WithBenefitsApplicationProps,
} from "../../hoc/withBenefitsApplication";

import { Ethnicity as EthnicityOptions } from "../../models/BenefitsApplication";
import InputChoiceGroup from "../../components/core/InputChoiceGroup";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { get } from "lodash";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";

export const fields = ["claim.ethnicity"];

export const Ethnicity = (props: WithBenefitsApplicationProps) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState({
    ethnicity: get(claim, "ethnicity") || EthnicityOptions.preferNotToAnswer,
  });

  const handleSave = () =>
    appLogic.benefitsApplications.update(claim.application_id, formState);

  const getFunctionalInputProps = useFunctionalInputProps({
    errors: appLogic.errors,
    formState,
    updateFields,
  });

  const ethnicity = get(formState, "ethnicity");

  return (
    <QuestionPage
      title={t("pages.claimsEthnicity.title")}
      dataCy="ethnicity-form"
      onSave={handleSave}
    >
      <InputChoiceGroup
        {...getFunctionalInputProps("ethnicity")}
        choices={[
          {
            checked: ethnicity === EthnicityOptions.preferNotToAnswer,
            label: t("pages.claimsEthnicity.choicePreferNotToAnswer"),
            value: EthnicityOptions.preferNotToAnswer,
          },
          {
            checked: ethnicity === EthnicityOptions.hispanicOrLatino,
            label: t("pages.claimsEthnicity.choiceHispanicOrLatino"),
            value: EthnicityOptions.hispanicOrLatino,
          },
          {
            checked: ethnicity === EthnicityOptions.notHispanicOrLatino,
            label: t("pages.claimsEthnicity.choiceNotHispanicOrLatino"),
            value: EthnicityOptions.notHispanicOrLatino,
          },
        ]}
        type="radio"
        label={t("pages.claimsEthnicity.sectionLabel")}
      />
    </QuestionPage>
  );
};

export default withBenefitsApplication(Ethnicity);
