import BenefitsApplication from "../../models/BenefitsApplication";
import ConcurrentLeave from "../../models/ConcurrentLeave";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import InputDate from "../../components/InputDate";
import LeaveDatesAlert from "../../components/LeaveDatesAlert";
import QuestionPage from "../../components/QuestionPage";
import React from "react";
import { get } from "lodash";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

export const fields = [
  "claim.concurrent_leave",
  "claim.concurrent_leave.is_for_current_employer",
  "claim.concurrent_leave.leave_start_date",
  "claim.concurrent_leave.leave_end_date",
];

interface ConcurrentLeavesDetailsProps {
  appLogic: any;
  claim: BenefitsApplication;
  query: any;
}

export const ConcurrentLeavesDetails = (
  props: ConcurrentLeavesDetailsProps
) => {
  const { t } = useTranslation();
  const { appLogic, claim } = props;
  const employer_fein = claim.employer_fein;

  const { formState, updateFields } = useFormState({
    concurrent_leave: new ConcurrentLeave(get(claim, "concurrent_leave")),
  });
  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  const handleSave = () => {
    return appLogic.benefitsApplications.update(
      claim.application_id,
      formState
    );
  };

  return (
    <QuestionPage
      title={t("pages.claimsConcurrentLeavesDetails.title")}
      onSave={handleSave}
    >
      <InputChoiceGroup
        {...getFunctionalInputProps("concurrent_leave.is_for_current_employer")}
        choices={[
          {
            label: t("pages.claimsConcurrentLeavesDetails.choiceYes"),
            checked:
              get(formState, "concurrent_leave.is_for_current_employer") ===
              true,
            value: "true",
          },
          {
            label: t("pages.claimsConcurrentLeavesDetails.choiceNo"),
            checked:
              get(formState, "concurrent_leave.is_for_current_employer") ===
              false,
            value: "false",
          },
        ]}
        type="radio"
        label={t("pages.claimsConcurrentLeavesDetails.sectionLabel", {
          employer_fein,
        })}
        hint={
          <React.Fragment>
            <LeaveDatesAlert
              showWaitingDayPeriod
              startDate={claim.leaveStartDate}
              endDate={claim.leaveEndDate}
            />
            <p>{t("pages.claimsConcurrentLeavesDetails.hintHeader")}</p>
          </React.Fragment>
        }
      />
      <InputDate
        {...getFunctionalInputProps("concurrent_leave.leave_start_date")}
        dayLabel={t("components.form.dateInputDayLabel")}
        monthLabel={t("components.form.dateInputMonthLabel")}
        yearLabel={t("components.form.dateInputYearLabel")}
        hint={t("components.form.dateInputExample")}
        label={t("pages.claimsConcurrentLeavesDetails.leaveStartDateLabel")}
      />
      <InputDate
        {...getFunctionalInputProps("concurrent_leave.leave_end_date")}
        dayLabel={t("components.form.dateInputDayLabel")}
        monthLabel={t("components.form.dateInputMonthLabel")}
        yearLabel={t("components.form.dateInputYearLabel")}
        hint={t("components.form.dateInputExample")}
        label={t("pages.claimsConcurrentLeavesDetails.leaveEndDateLabel")}
      />
    </QuestionPage>
  );
};

export default withBenefitsApplication(ConcurrentLeavesDetails);
