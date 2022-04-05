import BenefitsApplication from "src/models/BenefitsApplication";
import React from "react";
import { Trans } from "react-i18next";
import dayjs from "dayjs";
import formatDate from "src/utils/formatDate";
import routes from "src/routes";
import { useTranslation } from "src/locales/i18n";

interface LeaveSpansBenefitYearsMessageProps {
  claim: BenefitsApplication;
}

export const LeaveSpansBenefitYearsMessage = (
  props: LeaveSpansBenefitYearsMessageProps
) => {
  const { t } = useTranslation();

  if (props.claim.computed_application_split === null) {
    throw new Error(
      "LeaveSpansBenefitYearsMessage called with claim.computed_application_split === null."
    );
  } else if (props.claim.computed_earliest_submission_date === null) {
    throw new Error(
      "LeaveSpansBenefitYearsMessage called with claim.computed_earliest_submission_date === null."
    );
  } else {
    const firstLeaveStartDate =
      props.claim.computed_application_split.application_dates_in_benefit_year
        .start_date;
    const firstLeaveEndDate =
      props.claim.computed_application_split.application_dates_in_benefit_year
        .end_date;
    const firstLeaveEarliestSubmissionDate =
      props.claim.computed_earliest_submission_date;

    const secondLeaveStartDate =
      props.claim.computed_application_split
        .application_dates_outside_benefit_year.start_date;
    const secondLeaveEndDate =
      props.claim.computed_application_split
        .application_dates_outside_benefit_year.end_date;
    const secondLeaveEarliestSubmissionDate =
      props.claim.computed_application_split
        .application_outside_benefit_year_submittable_on;

    const currentBenefitYearStartDate =
      props.claim.computed_application_split?.crossed_benefit_year
        .benefit_year_start_date;
    const currentBenefitYearEndDate =
      props.claim.computed_application_split?.crossed_benefit_year
        .benefit_year_end_date;

    const today = dayjs().format("YYYY-MM-DD");
    const firstCanBeSubmitted = firstLeaveEarliestSubmissionDate <= today;
    const secondCanBeSubmitted = secondLeaveEarliestSubmissionDate <= today;

    interface IntroductionProps {
      startDate: string;
      endDate: string;
    }

    const Introduction = (props: IntroductionProps) => {
      return (
        <Trans
          i18nKey="shared.claimsLeaveSpansBenefitYears.introduction"
          values={{
            startDate: formatDate(props.startDate).short(),
            endDate: formatDate(props.endDate).short(),
          }}
          components={{
            "benefit-year-guide-link": (
              <a
                href={routes.external.massgov.importantTermsToKnow}
                rel="noopener noreferrer"
                target="_blank"
              />
            ),
          }}
        />
      );
    };

    interface MessageProps {
      currentBenefitYearStartDate: string;
      currentBenefitYearEndDate: string;
      firstLeaveStartDate: string;
      firstLeaveEndDate: string;
      firstLeaveEarliestSubmissionDate: string;
      secondLeaveStartDate: string;
      secondLeaveEndDate: string;
      secondLeaveEarliestSubmissionDate: string;
    }

    const BothCanBeSubmittedMessage = (props: MessageProps) => {
      return (
        <React.Fragment>
          <Introduction
            startDate={props.currentBenefitYearStartDate}
            endDate={props.currentBenefitYearEndDate}
          />
          <ul>
            <li>
              <Trans
                i18nKey="shared.claimsLeaveSpansBenefitYears.currentBenefitYearLeaveDates"
                values={{
                  startDate: formatDate(props.firstLeaveStartDate).short(),
                  endDate: formatDate(props.firstLeaveEndDate).short(),
                }}
              />
            </li>
            <li>
              <Trans
                i18nKey="shared.claimsLeaveSpansBenefitYears.newBenefitYearLeaveDates"
                values={{
                  startDate: formatDate(props.secondLeaveStartDate).short(),
                  endDate: formatDate(props.secondLeaveEndDate).short(),
                }}
              />
            </li>
          </ul>
          <p>
            {t(
              "shared.claimsLeaveSpansBenefitYears.bothCanBeSubmittedReviewedSeparately"
            )}
          </p>
          <ul>
            <li>
              <p>
                {t(
                  "shared.claimsLeaveSpansBenefitYears.bothCanBeSubmittedDeterminationMayBeDifferent"
                )}
              </p>
            </li>
            <li>
              <p>
                <Trans
                  i18nKey="shared.claimsLeaveSpansBenefitYears.bothCanBeSubmittedBenefitsCalculatedSeparately"
                  components={{
                    "how-benefit-amounts-are-calculated-link": (
                      <a
                        href={
                          routes.external.massgov
                            .benefitsGuide_howBenefitsAmountsAreCalculated
                        }
                        rel="noopener noreferrer"
                        target="_blank"
                      />
                    ),
                  }}
                />
              </p>
            </li>
            <li>
              <p>
                <Trans
                  i18nKey="shared.claimsLeaveSpansBenefitYears.bothCanBeSubmittedSevenDayWaitingPeriod"
                  components={{
                    "seven-day-waiting-period-link": (
                      <a
                        href={routes.external.massgov.importantTermsToKnow}
                        rel="noopener noreferrer"
                        target="_blank"
                      />
                    ),
                  }}
                />
              </p>
            </li>
          </ul>
        </React.Fragment>
      );
    };

    const OnlyFirstCanBeSubmittedMessage = (props: MessageProps) => {
      return (
        <React.Fragment>
          <Introduction
            startDate={props.currentBenefitYearStartDate}
            endDate={props.currentBenefitYearEndDate}
          />
          <p>
            <Trans
              i18nKey="shared.claimsLeaveSpansBenefitYears.currentBenefitYearLeaveDates"
              values={{
                startDate: formatDate(props.firstLeaveStartDate).short(),
                endDate: formatDate(props.firstLeaveEndDate).short(),
              }}
            />
          </p>
          <ul>
            <li>
              {t(
                "shared.claimsLeaveSpansBenefitYears.secondCannotBeSubmittedCurrent"
              )}
            </li>
          </ul>
          <p>
            <Trans
              i18nKey="shared.claimsLeaveSpansBenefitYears.newBenefitYearLeaveDates"
              values={{
                startDate: formatDate(props.secondLeaveStartDate).short(),
                endDate: formatDate(props.secondLeaveEndDate).short(),
              }}
            />
          </p>
          <ul>
            <li>
              <Trans
                i18nKey="shared.claimsLeaveSpansBenefitYears.secondCannotBeSubmittedNew"
                values={{
                  submittableDate: formatDate(
                    props.secondLeaveEarliestSubmissionDate
                  ).short(),
                }}
              />
            </li>
          </ul>
        </React.Fragment>
      );
    };

    const NeitherCanBeSubmittedMessage = (props: MessageProps) => {
      return (
        <React.Fragment>
          <Introduction
            startDate={props.currentBenefitYearStartDate}
            endDate={props.currentBenefitYearEndDate}
          />
          <p>
            <Trans
              i18nKey="shared.claimsLeaveSpansBenefitYears.currentBenefitYearLeaveDates"
              values={{
                startDate: formatDate(props.firstLeaveStartDate).short(),
                endDate: formatDate(props.firstLeaveEndDate).short(),
              }}
            />
          </p>
          <ul>
            <li>
              <Trans
                i18nKey="shared.claimsLeaveSpansBenefitYears.bothCannotBeSubmittedCurrent"
                values={{
                  submittableDate: formatDate(
                    props.firstLeaveEarliestSubmissionDate
                  ).short(),
                }}
              />
            </li>
          </ul>
          <p>
            <Trans
              i18nKey="shared.claimsLeaveSpansBenefitYears.newBenefitYearLeaveDates"
              values={{
                startDate: formatDate(props.secondLeaveStartDate).short(),
                endDate: formatDate(props.secondLeaveEndDate).short(),
              }}
            />
          </p>
          <ul>
            <li>
              <Trans
                i18nKey="shared.claimsLeaveSpansBenefitYears.bothCannotBeSubmittedNew"
                values={{
                  submittableDate: formatDate(
                    props.secondLeaveEarliestSubmissionDate
                  ).short(),
                }}
              />
            </li>
          </ul>
          <p>
            {t(
              "shared.claimsLeaveSpansBenefitYears.bothCannotBeSubmittedReminder"
            )}
          </p>
        </React.Fragment>
      );
    };

    if (firstCanBeSubmitted && secondCanBeSubmitted) {
      return (
        <BothCanBeSubmittedMessage
          currentBenefitYearStartDate={currentBenefitYearStartDate}
          currentBenefitYearEndDate={currentBenefitYearEndDate}
          firstLeaveStartDate={firstLeaveStartDate}
          firstLeaveEndDate={firstLeaveEndDate}
          firstLeaveEarliestSubmissionDate={firstLeaveEarliestSubmissionDate}
          secondLeaveStartDate={secondLeaveStartDate}
          secondLeaveEndDate={secondLeaveEndDate}
          secondLeaveEarliestSubmissionDate={secondLeaveEarliestSubmissionDate}
        />
      );
    } else if (firstCanBeSubmitted && !secondCanBeSubmitted) {
      return (
        <OnlyFirstCanBeSubmittedMessage
          currentBenefitYearStartDate={currentBenefitYearStartDate}
          currentBenefitYearEndDate={currentBenefitYearEndDate}
          firstLeaveStartDate={firstLeaveStartDate}
          firstLeaveEndDate={firstLeaveEndDate}
          firstLeaveEarliestSubmissionDate={firstLeaveEarliestSubmissionDate}
          secondLeaveStartDate={secondLeaveStartDate}
          secondLeaveEndDate={secondLeaveEndDate}
          secondLeaveEarliestSubmissionDate={secondLeaveEarliestSubmissionDate}
        />
      );
    } else {
      return (
        <NeitherCanBeSubmittedMessage
          currentBenefitYearStartDate={currentBenefitYearStartDate}
          currentBenefitYearEndDate={currentBenefitYearEndDate}
          firstLeaveStartDate={firstLeaveStartDate}
          firstLeaveEndDate={firstLeaveEndDate}
          firstLeaveEarliestSubmissionDate={firstLeaveEarliestSubmissionDate}
          secondLeaveStartDate={secondLeaveStartDate}
          secondLeaveEndDate={secondLeaveEndDate}
          secondLeaveEarliestSubmissionDate={secondLeaveEarliestSubmissionDate}
        />
      );
    }
  }
};

export default LeaveSpansBenefitYearsMessage;
