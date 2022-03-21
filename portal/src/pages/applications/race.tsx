import withBenefitsApplication, {
  WithBenefitsApplicationProps,
} from "../../hoc/withBenefitsApplication";

import InputChoiceGroup from "../../components/core/InputChoiceGroup";
import QuestionPage from "../../components/QuestionPage";
import { Race as RaceOptions } from "../../models/BenefitsApplication";
import React from "react";
import { get } from "lodash";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";

export const fields = ["claim.race"];

export const Race = (props: WithBenefitsApplicationProps) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState({
    race: get(claim, "race") || RaceOptions.preferNotToAnswer,
  });

  const handleSave = () =>
    appLogic.benefitsApplications.update(claim.application_id, formState);

  const getFunctionalInputProps = useFunctionalInputProps({
    errors: appLogic.errors,
    formState,
    updateFields,
  });

  const race = get(formState, "race");

  return (
    <QuestionPage
      title={t("pages.claimsRace.title")}
      dataCy="race-form"
      onSave={handleSave}
    >
      <InputChoiceGroup
        {...getFunctionalInputProps("race")}
        choices={[
          {
            checked: race === RaceOptions.preferNotToAnswer,
            label: t("pages.claimsRace.choicePreferNotToAnswer"),
            value: RaceOptions.preferNotToAnswer,
          },
          {
            checked: race === RaceOptions.americanIndianAlaskaNative,
            label: t("pages.claimsRace.choiceAmericanIndianAlaskaNative"),
            value: RaceOptions.americanIndianAlaskaNative,
          },
          {
            checked: race === RaceOptions.asianAsianAmerican,
            label: t("pages.claimsRace.choiceAsianAsianAmerican"),
            value: RaceOptions.asianAsianAmerican,
          },
          {
            checked: race === RaceOptions.blackAfricanAmerican,
            label: t("pages.claimsRace.choiceBlackAfricanAmerican"),
            value: RaceOptions.blackAfricanAmerican,
          },
          {
            checked: race === RaceOptions.nativeHawaiianOtherPacificIslander,
            label: t(
              "pages.claimsRace.choiceNativeHawaiianOtherPacificIslander"
            ),
            value: RaceOptions.nativeHawaiianOtherPacificIslander,
          },
          {
            checked: race === RaceOptions.white,
            label: t("pages.claimsRace.choiceWhite"),
            value: RaceOptions.white,
          },
        ]}
        type="checkbox"
        label={t("pages.claimsRace.sectionLabel")}
        hint={t("pages.claimsRace.sectionLabelHint")}
      />
    </QuestionPage>
  );
};

export default withBenefitsApplication(Race);
