import withBenefitsApplication, {
  WithBenefitsApplicationProps,
} from "../../hoc/withBenefitsApplication";

import InputDate from "../../components/core/InputDate";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { get, pick } from "lodash";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import Fieldset from "src/components/core/Fieldset";
import ConditionalContent from "src/components/ConditionalContent";
import FormLabel from "src/components/core/FormLabel";

export const fields = [
  "claim.additional_user_not_found_info.date_of_separation",
];

/**
 * A form page to collect employee start date.
 */
export const DateOfSeparation = (props: WithBenefitsApplicationProps) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState(
    pick(props, fields).claim?.additional_user_not_found_info
  );

  const handleSave = () =>
    appLogic.benefitsApplications.update(claim.application_id, {
      additional_user_not_found_info: {
        ...claim?.additional_user_not_found_info,
        ...formState,
      },
    });

  const getFunctionalInputProps = useFunctionalInputProps({
    errors: appLogic.errors,
    formState,
    updateFields,
  });

  const date_of_separation =
    get(formState, "additional_user_not_found_info.date_of_separation") ?? null;

  console.log(formState);

  return (
    <QuestionPage
      title={t("pages.claimsEmploymentStatus.title")}
      onSave={handleSave}
    >
      <Fieldset>
        <ConditionalContent visible={true}>
          <FormLabel component="legend">
            {t("pages.claimsOrganizationUnit.sectionLabel")}
          </FormLabel>
        </ConditionalContent>
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
      </Fieldset>
    </QuestionPage>
  );
};

export default withBenefitsApplication(DateOfSeparation);
