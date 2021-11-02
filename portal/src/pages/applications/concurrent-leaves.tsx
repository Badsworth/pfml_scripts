import React, { Fragment } from "react";
import { AppLogic } from "../../hooks/useAppLogic";
import BenefitsApplication from "../../models/BenefitsApplication";
import Details from "../../components/Details";
import IconHeading from "../../components/IconHeading";
import InputChoiceGroup from "../../components/InputChoiceGroup";
import LeaveDatesAlert from "../../components/LeaveDatesAlert";
import QuestionPage from "../../components/QuestionPage";
import { Trans } from "react-i18next";
import { pick } from "lodash";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

export const fields = ["claim.has_concurrent_leave"];

interface ConcurrentLeavesProps {
  appLogic: AppLogic;
  claim: BenefitsApplication;
  query: { [key: string]: string };
}

export const ConcurrentLeaves = (props: ConcurrentLeavesProps) => {
  const { t } = useTranslation();
  const {
    appLogic,
    claim,
    claim: { leave_details },
  } = props;

  const { formState, updateFields } = useFormState(pick(props, fields).claim);

  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  const handleSave = () => {
    if (formState.has_concurrent_leave === false && claim.concurrent_leave) {
      formState.concurrent_leave = null;
    }
    return appLogic.benefitsApplications.update(
      claim.application_id,
      formState
    );
  };

  // Determines leave type
  const isContinuousLeave = Boolean(
    leave_details?.continuous_leave_periods?.length
  );
  const isIntermittentLeave = Boolean(
    leave_details?.intermittent_leave_periods?.length
  );
  const isReducedLeave = Boolean(
    leave_details?.reduced_schedule_leave_periods?.length
  );

  // Determines intro & details to be displayed
  const isContinuousLeaveIntro =
    isContinuousLeave && !isReducedLeave && !isIntermittentLeave;
  const isContinuousReducedIntro = isContinuousLeave && isReducedLeave;
  const isReducedOrIntermittentIntro =
    (isReducedLeave && !isContinuousLeave) || isIntermittentLeave;
  const isQualifyingReasonDetails =
    isContinuousReducedIntro || !isContinuousLeave;

  // Gets context for intro trans
  const getIntroContext = () => {
    if (isContinuousLeaveIntro) return "Continuous";
    else if (isReducedOrIntermittentIntro) return "ReducedOrIntermittent";
    else if (isContinuousReducedIntro) return "ContinuousReduced";
  };

  return (
    <QuestionPage
      title={t("pages.claimsConcurrentLeaves.title")}
      onSave={handleSave}
    >
      <InputChoiceGroup
        {...getFunctionalInputProps("has_concurrent_leave")}
        choices={[
          {
            checked: formState.has_concurrent_leave === true,
            hint: t("pages.claimsConcurrentLeaves.choiceYesHint"),
            label: t("pages.claimsConcurrentLeaves.choiceYes"),
            value: "true",
          },
          {
            checked: formState.has_concurrent_leave === false,
            hint: t("pages.claimsConcurrentLeaves.choiceNoHint"),
            label: t("pages.claimsConcurrentLeaves.choiceNo"),
            value: "false",
          },
        ]}
        label={t("pages.claimsConcurrentLeaves.sectionLabel")}
        type="radio"
        hint={
          <div className="margin-bottom-5">
            <LeaveDatesAlert
              startDate={claim.leaveStartDate}
              endDate={claim.leaveEndDate}
              showWaitingDayPeriod
            />

            <IconHeading name="check_circle">
              {t("pages.claimsConcurrentLeaves.hintWhatKindHeading")}
            </IconHeading>

            <div className="margin-top-1 margin-left-3 margin-bottom-2">
              <Trans
                i18nKey={`pages.claimsConcurrentLeaves.intro`}
                components={{ div: <div />, li: <li />, ul: <ul /> }}
                tOptions={{ context: getIntroContext() }}
              />
            </div>

            {isContinuousReducedIntro && (
              <Fragment>
                <IconHeading name="check_circle">
                  {t(
                    "pages.claimsConcurrentLeaves.whenToReportContinuousLeave"
                  )}
                </IconHeading>
                <div className="margin-top-1 margin-left-3 margin-bottom-2">
                  {t("pages.claimsConcurrentLeaves.typesOfLeaveToReport")}
                </div>

                <IconHeading name="check_circle">
                  {t("pages.claimsConcurrentLeaves.whenToReportReducedLeave")}
                </IconHeading>
                <div className="margin-top-1 margin-left-3 margin-bottom-2">
                  <Trans
                    i18nKey="pages.claimsConcurrentLeaves.intro"
                    components={{ div: <div />, li: <li />, ul: <ul /> }}
                    tOptions={{ context: "ReducedOrIntermittent" }}
                  />
                </div>
              </Fragment>
            )}
            {isQualifyingReasonDetails && (
              <Details
                label={t(
                  "pages.claimsConcurrentLeaves.hintWhenToReportDetailsLabel"
                )}
              >
                <Trans
                  i18nKey="pages.claimsConcurrentLeaves.hintWhenToReportDetailsBody"
                  components={{ ul: <ul className="usa-list" />, li: <li /> }}
                />
              </Details>
            )}

            <IconHeading name="cancel">
              {t("pages.claimsConcurrentLeaves.dontNeedToReport")}
            </IconHeading>
          </div>
        }
      />
    </QuestionPage>
  );
};

export default withBenefitsApplication(ConcurrentLeaves);
