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
  "claim.additional_user_not_found_info.date_of_separation",
];

/**
 * A form page to collect employee start date.
 */
export const DateOfSeparation = (props: WithBenefitsApplicationProps) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const defaultFormState = pick(props, fields).claim
    ?.additional_user_not_found_info;

  const { formState, getField, updateFields, clearField } = useFormState({
    ...defaultFormState,
    still_work_for_employer: defaultFormState
      ? defaultFormState?.date_of_separation === null
      : true,
  });

  const handleSave = () =>
    appLogic.benefitsApplications.update(claim.application_id, {
      additional_user_not_found_info: {
        ...claim?.additional_user_not_found_info,
        date_of_separation: formState.date_of_separation,
      },
    });

  const getFunctionalInputProps = useFunctionalInputProps({
    errors: appLogic.errors,
    formState,
    updateFields,
  });

  const still_work_for_employer =
    get(formState, "still_work_for_employer") ?? null;

  return (
    <QuestionPage
      title={t("pages.claimsEmploymentStatus.title")}
      onSave={handleSave}
    >
      <Fieldset>
        <InputChoiceGroup
          {...getFunctionalInputProps("still_work_for_employer")}
          choices={[
            {
              checked: still_work_for_employer === true,
              label: t(
                "pages.claimsAdditionalUserNotFoundInfo.recentlyAcquiredOrMergedYesLabel"
              ),
              value: "true",
            },
            {
              checked: still_work_for_employer === false,
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
          visible={!still_work_for_employer}
          getField={getField}
          clearField={clearField}
          updateFields={updateFields}
          fieldNamesClearedWhenHidden={["date_of_separation"]}
        >
          <InputDate
            {...getFunctionalInputProps("date_of_separation")}
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
