import { get, pick } from "lodash";
import withBenefitsApplication, {
  WithBenefitsApplicationProps,
} from "../../hoc/withBenefitsApplication";

import ConditionalContent from "src/components/ConditionalContent";
import Fieldset from "src/components/core/Fieldset";
import InputChoiceGroup from "src/components/core/InputChoiceGroup";
import InputDate from "../../components/core/InputDate";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";

export const fields = [
  "claim.additional_user_not_found_info.currently_employed",
  "claim.additional_user_not_found_info.date_of_separation",
];

/**
 * A form page to collect employee start date.
 */
export const DateOfSeparation = (props: WithBenefitsApplicationProps) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const { clearField, formState, getField, updateFields } = useFormState(
    pick(props, ["claim.additional_user_not_found_info"]).claim
  );

  const handleSave = () =>
    appLogic.benefitsApplications.update(claim.application_id, formState);

  const getFunctionalInputProps = useFunctionalInputProps({
    errors: appLogic.errors,
    formState,
    updateFields,
  });

  const currently_employed = get(
    formState,
    "additional_user_not_found_info.currently_employed"
  );

  return (
    <QuestionPage
      title={t("pages.claimsEmploymentStatus.title")}
      onSave={handleSave}
    >
      <Fieldset>
        <InputChoiceGroup
          {...getFunctionalInputProps(
            "additional_user_not_found_info.currently_employed"
          )}
          choices={[
            {
              checked: currently_employed === true,
              label: t(
                "pages.claimsAdditionalUserNotFoundInfo.recentlyAcquiredOrMergedYesLabel"
              ),
              value: "true",
            },
            {
              checked: currently_employed === false,
              label: t(
                "pages.claimsAdditionalUserNotFoundInfo.recentlyAcquiredOrMergedNoLabel"
              ),
              value: "false",
            },
          ]}
          type="radio"
          label={t(
            "pages.claimsAdditionalUserNotFoundInfo.currentlyWorkAtEmployerLabel"
          )}
        />
        <ConditionalContent
          clearField={clearField}
          fieldNamesClearedWhenHidden={[
            "additional_user_not_found_info.date_of_separation",
          ]}
          getField={getField}
          updateFields={updateFields}
          visible={currently_employed === false}
        >
          <InputDate
            {...getFunctionalInputProps(
              "additional_user_not_found_info.date_of_separation"
            )}
            label={t(
              "pages.claimsAdditionalUserNotFoundInfo.dateOfSeparationLabel"
            )}
            example={t("components.form.dateInputExample")}
            dayLabel={t("components.form.dateInputDayLabel")}
            monthLabel={t("components.form.dateInputMonthLabel")}
            yearLabel={t("components.form.dateInputYearLabel")}
          />
        </ConditionalContent>
      </Fieldset>
    </QuestionPage>
  );
};

export default withBenefitsApplication(DateOfSeparation);
