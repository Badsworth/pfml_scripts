import { get, pick } from "lodash";
import withBenefitsApplication, {
  WithBenefitsApplicationProps,
} from "../../hoc/withBenefitsApplication";
import InputChoiceGroup from "../../components/core/InputChoiceGroup";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";

export const fields = [
  "claim.additional_user_not_found_info.recently_acquired_or_merged",
];

export const RecentlyAcquiredOrMerged = (
  props: WithBenefitsApplicationProps
) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  // const { formState, updateFields } = useFormState({
  //  gender: get(claim, "gender") || GenderDescription.preferNotToAnswer,
  // });
  const { formState, updateFields } = useFormState(pick(props, fields).claim);

  const handleSave = () =>
    appLogic.benefitsApplications.update(claim.application_id, formState);

  const getFunctionalInputProps = useFunctionalInputProps({
    errors: appLogic.errors,
    formState,
    updateFields,
  });

  get(formState, "gender");

  return (
    <QuestionPage
      title={t("pages.claimsRecentlyAcquiredOrMerged.title")}
      dataCy="gender-form"
      onSave={handleSave}
    >
      <InputChoiceGroup
        {...getFunctionalInputProps("gender")}
        choices={
          [
            /*
          {
            checked: gender === GenderDescription.preferNotToAnswer,
            label: t("pages.claimsGender.choicePreferNotToAnswer"),
            value: GenderDescription.preferNotToAnswer,
          },
          */
          ]
        }
        type="radio"
        label={t("pages.claimsRecentlyAcquiredOrMerged.sectionLabel")}
        hint={t("pages.claimsRecentlyAcquiredOrMerged.sectionLabelHint")}
      />
    </QuestionPage>
  );
};

export default withBenefitsApplication(RecentlyAcquiredOrMerged);
