import { AppLogic } from "../../hooks/useAppLogic";
import BenefitsApplication from "../../models/BenefitsApplication";
import InputDate from "../../components/InputDate";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { pick } from "lodash";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

export const fields = ["claim.date_of_birth"];

interface DateOfBirthProps {
  appLogic: AppLogic;
  claim: BenefitsApplication;
  query: {
    claim_id?: string;
  };
}

export const DateOfBirth = (props: DateOfBirthProps) => {
  const { appLogic, claim } = props;
  const { t } = useTranslation();

  const { formState, updateFields } = useFormState(pick(props, fields).claim);

  const handleSave = () =>
    appLogic.benefitsApplications.update(claim.application_id, formState);

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  return (
    <QuestionPage
      title={t("pages.claimsDateOfBirth.title")}
      onSave={handleSave}
    >
      <InputDate
        {...getFunctionalInputProps("date_of_birth")}
        label={t("pages.claimsDateOfBirth.sectionLabel")}
        example={t("components.form.dateInputExample")}
        dayLabel={t("components.form.dateInputDayLabel")}
        monthLabel={t("components.form.dateInputMonthLabel")}
        yearLabel={t("components.form.dateInputYearLabel")}
      />
    </QuestionPage>
  );
};

export default withBenefitsApplication(DateOfBirth);
