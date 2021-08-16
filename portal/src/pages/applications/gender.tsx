import BenefitsApplication, {
  Gender as GenderDescription,
} from "../../models/BenefitsApplication";

import InputChoiceGroup from "../../components/InputChoiceGroup";
import PropTypes from "prop-types";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { get } from "lodash";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

export const fields = ["claim.gender"];

export const Gender = (props) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();
  // @ts-expect-error ts-migrate(2339) FIXME: Property 'formState' does not exist on type 'FormS... Remove this comment to see the full error message
  const { formState, updateFields } = useFormState({
    gender: get(claim, "gender") || GenderDescription.preferNotToAnswer,
  });

  const handleSave = () =>
    appLogic.benefitsApplications.update(claim.application_id, formState);

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  const gender = get(formState, "gender");

  return (
    <QuestionPage
      title={t("pages.claimsGender.title")}
      dataCy="gender-form"
      onSave={handleSave}
    >
      <InputChoiceGroup
        {...getFunctionalInputProps("gender")}
        choices={[
          {
            checked: gender === GenderDescription.preferNotToAnswer,
            label: t("pages.claimsGender.choicePreferNotToAnswer"),
            value: GenderDescription.preferNotToAnswer,
          },
          {
            checked: gender === GenderDescription.man,
            label: t("pages.claimsGender.choiceMan"),
            value: GenderDescription.man,
          },
          {
            checked: gender === GenderDescription.woman,
            label: t("pages.claimsGender.choiceWoman"),
            value: GenderDescription.woman,
          },
          {
            checked: gender === GenderDescription.nonbinary,
            label: t("pages.claimsGender.choiceNonbinary"),
            value: GenderDescription.nonbinary,
          },
          {
            checked: gender === GenderDescription.genderNotListed,
            label: t("pages.claimsGender.choiceGenderNotListed"),
            value: GenderDescription.genderNotListed,
          },
        ]}
        type="radio"
        label={t("pages.claimsGender.sectionLabel")}
        hint={t("pages.claimsGender.sectionLabelHint")}
      />
    </QuestionPage>
  );
};

Gender.propTypes = {
  appLogic: PropTypes.object.isRequired,
  claim: PropTypes.instanceOf(BenefitsApplication).isRequired,
};

export default withBenefitsApplication(Gender);
