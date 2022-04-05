import React, { Fragment } from "react";
import withBenefitsApplication, {
  WithBenefitsApplicationProps,
} from "../../hoc/withBenefitsApplication";

import Details from "../../components/core/Details";
import Heading from "../../components/core/Heading";
import Icon from "../../components/core/Icon";
import InputChoiceGroup from "../../components/core/InputChoiceGroup";
import LeaveDatesAlert from "../../components/LeaveDatesAlert";
import QuestionPage from "../../components/QuestionPage";
import { Trans } from "react-i18next";
import { pick } from "lodash";
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps";
import { useTranslation } from "../../locales/i18n";

export const fields = ["claim.has_concurrent_leave"];

export const ConcurrentLeaves = (props: WithBenefitsApplicationProps) => {
  const { t } = useTranslation();
  const { appLogic, claim } = props;

  const { formState, updateFields } = useFormState(pick(props, fields).claim);

  const getFunctionalInputProps = useFunctionalInputProps({
    errors: appLogic.errors,
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

  const { isContinuous, isIntermittent, isReducedSchedule } = claim;

  // Determines intro & details to be displayed
  const isContinuousLeaveIntro =
    isContinuous && !isReducedSchedule && !isIntermittent;
  const isContinuousReducedIntro = isContinuous && isReducedSchedule;
  const isReducedOrIntermittentIntro =
    (isReducedSchedule && !isContinuous) || isIntermittent;
  const isQualifyingReasonDetails = isContinuousReducedIntro || !isContinuous;

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
        label={
          <Heading level="2" size="1">
            {t("pages.claimsConcurrentLeaves.sectionLabel")}
          </Heading>
        }
        type="radio"
        hint={
          <div className="margin-bottom-5">
            <LeaveDatesAlert
              startDate={claim.leaveStartDate}
              endDate={claim.leaveEndDate}
              showWaitingDayPeriod={!isIntermittent}
              applicationSplit={claim.computed_application_split}
            />
            <Heading level="3">
              <Icon
                name="check"
                size={3}
                className="text-secondary text-middle margin-right-1 margin-top-neg-05"
              />
              {t("pages.claimsConcurrentLeaves.hintWhatKindHeading")}
            </Heading>

            <div className="margin-top-1 margin-left-4 margin-bottom-2">
              <Trans
                i18nKey={`pages.claimsConcurrentLeaves.intro`}
                components={{ div: <div />, li: <li />, ul: <ul /> }}
                tOptions={{ context: getIntroContext() }}
              />
            </div>

            {isContinuousReducedIntro && (
              <Fragment>
                <Heading level="3">
                  <Icon
                    name="check"
                    size={3}
                    className="text-secondary text-middle margin-right-1 margin-top-neg-05"
                  />
                  {t(
                    "pages.claimsConcurrentLeaves.whenToReportContinuousLeave"
                  )}
                </Heading>
                <div className="margin-top-1 margin-left-3 margin-bottom-2">
                  {t("pages.claimsConcurrentLeaves.typesOfLeaveToReport")}
                </div>
                <Heading level="3">
                  <Icon
                    name="check"
                    size={3}
                    className="text-secondary text-middle margin-right-1 margin-top-neg-05"
                  />
                  {t("pages.claimsConcurrentLeaves.whenToReportReducedLeave")}
                </Heading>
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
            <Heading level="3">
              <Icon
                name="close"
                size={3}
                className="text-error text-middle margin-right-1 margin-top-neg-05"
              />
              {t("pages.claimsConcurrentLeaves.dontNeedToReport", {
                context: isIntermittent ? "intermittentLeave" : null,
              })}
            </Heading>
          </div>
        }
      />
    </QuestionPage>
  );
};

export default withBenefitsApplication(ConcurrentLeaves);
