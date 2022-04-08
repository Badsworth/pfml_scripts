import ApplicationSplit from "src/models/ApplicationSplit";
import React from "react";
import { Trans } from "react-i18next";
import dayjs from "dayjs";
import formatDate from "src/utils/formatDate";
import routes from "src/routes";
import { useTranslation } from "src/locales/i18n";

interface LeaveSpansBenefitYearsMessageProps {
  computed_application_split: ApplicationSplit;
  computed_earliest_submission_date: string;
  final_content_before_submit?: boolean;
}

export const LeaveSpansBenefitYearsMessage = (
  props: LeaveSpansBenefitYearsMessageProps
) => {
  const { t } = useTranslation();

  const firstLeaveStartDate =
    props.computed_application_split.application_dates_in_benefit_year
      .start_date;
  const firstLeaveEndDate =
    props.computed_application_split.application_dates_in_benefit_year.end_date;
  const firstLeaveEarliestSubmissionDate =
    props.computed_earliest_submission_date;

  const secondLeaveStartDate =
    props.computed_application_split.application_dates_outside_benefit_year
      .start_date;
  const secondLeaveEndDate =
    props.computed_application_split.application_dates_outside_benefit_year
      .end_date;
  const secondLeaveEarliestSubmissionDate =
    props.computed_application_split
      .application_outside_benefit_year_submittable_on;

  const currentBenefitYearStartDate =
    props.computed_application_split.crossed_benefit_year
      .benefit_year_start_date;
  const currentBenefitYearEndDate =
    props.computed_application_split.crossed_benefit_year.benefit_year_end_date;

  const final_content_before_submit = props.final_content_before_submit;

  const today = dayjs().format("YYYY-MM-DD");
  const firstCanBeSubmitted = firstLeaveEarliestSubmissionDate <= today;
  const secondCanBeSubmitted = secondLeaveEarliestSubmissionDate <= today;

  interface IntroductionProps {
    startDate: string;
    endDate: string;
  }

  const Introduction = (props: IntroductionProps) => {
    return (
      <p>
        <Trans
          i18nKey="components.claimsLeaveSpansBenefitYears.introduction"
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
      </p>
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

  const getFinalContentBeforeSubmitMessage = () => {
    return (
      <ul className="usa-list">
        <li>
          <p>
            <Trans
              i18nKey="components.claimsLeaveSpansBenefitYears.secondCannotBeSubmittedCurrentFinalContentPart1"
              components={{
                "contact-center-phone-link": (
                  <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
                ),
              }}
            />
          </p>
        </li>
        <li>
          <p>
            {t(
              "components.claimsLeaveSpansBenefitYears.secondCannotBeSubmittedCurrentFinalContentPart2"
            )}
          </p>
        </li>
        <li>
          <p>
            {t(
              "components.claimsLeaveSpansBenefitYears.secondCannotBeSubmittedCurrentFinalContentPart3"
            )}
          </p>
        </li>
      </ul>
    );
  };

  const BothCanBeSubmittedMessage = (props: MessageProps) => {
    return (
      <React.Fragment>
        <Introduction
          startDate={props.currentBenefitYearStartDate}
          endDate={props.currentBenefitYearEndDate}
        />
        <ul className="usa-list">
          <li>
            <p>
              <Trans
                i18nKey="components.claimsLeaveSpansBenefitYears.currentBenefitYearLeaveDates"
                values={{
                  startDate: formatDate(props.firstLeaveStartDate).short(),
                  endDate: formatDate(props.firstLeaveEndDate).short(),
                }}
              />
            </p>
          </li>
          <li>
            <p>
              <Trans
                i18nKey="components.claimsLeaveSpansBenefitYears.newBenefitYearLeaveDates"
                values={{
                  startDate: formatDate(props.secondLeaveStartDate).short(),
                  endDate: formatDate(props.secondLeaveEndDate).short(),
                }}
              />
            </p>
          </li>
        </ul>
        <p>
          {t(
            "components.claimsLeaveSpansBenefitYears.bothCanBeSubmittedReviewedSeparately"
          )}
        </p>
        <ul className="usa-list">
          <li>
            <p>
              {t(
                "components.claimsLeaveSpansBenefitYears.bothCanBeSubmittedDeterminationMayBeDifferent"
              )}
            </p>
          </li>
          <li>
            <p>
              <Trans
                i18nKey="components.claimsLeaveSpansBenefitYears.bothCanBeSubmittedBenefitsCalculatedSeparately"
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
                i18nKey="components.claimsLeaveSpansBenefitYears.bothCanBeSubmittedSevenDayWaitingPeriod"
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
            i18nKey="components.claimsLeaveSpansBenefitYears.currentBenefitYearLeaveDates"
            values={{
              startDate: formatDate(props.firstLeaveStartDate).short(),
              endDate: formatDate(props.firstLeaveEndDate).short(),
            }}
          />
        </p>
        {final_content_before_submit && getFinalContentBeforeSubmitMessage()}
        {!final_content_before_submit && (
          <ul className="usa-list">
            <li>
              <p>
                {t(
                  "components.claimsLeaveSpansBenefitYears.secondCannotBeSubmittedCurrent"
                )}
              </p>
            </li>
          </ul>
        )}
        <p>
          <Trans
            i18nKey="components.claimsLeaveSpansBenefitYears.newBenefitYearLeaveDates"
            values={{
              startDate: formatDate(props.secondLeaveStartDate).short(),
              endDate: formatDate(props.secondLeaveEndDate).short(),
            }}
          />
        </p>
        <ul className="usa-list">
          <li>
            <p>
              <Trans
                i18nKey="components.claimsLeaveSpansBenefitYears.secondCannotBeSubmittedNew"
                values={{
                  submittableDate: formatDate(
                    props.secondLeaveEarliestSubmissionDate
                  ).short(),
                }}
              />
            </p>
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
            i18nKey="components.claimsLeaveSpansBenefitYears.currentBenefitYearLeaveDates"
            values={{
              startDate: formatDate(props.firstLeaveStartDate).short(),
              endDate: formatDate(props.firstLeaveEndDate).short(),
            }}
          />
        </p>
        <ul className="usa-list">
          <li>
            <p>
              <Trans
                i18nKey="components.claimsLeaveSpansBenefitYears.bothCannotBeSubmittedCurrent"
                values={{
                  submittableDate: formatDate(
                    props.firstLeaveEarliestSubmissionDate
                  ).short(),
                }}
              />
            </p>
          </li>
        </ul>
        <p>
          <Trans
            i18nKey="components.claimsLeaveSpansBenefitYears.newBenefitYearLeaveDates"
            values={{
              startDate: formatDate(props.secondLeaveStartDate).short(),
              endDate: formatDate(props.secondLeaveEndDate).short(),
            }}
          />
        </p>
        <ul className="usa-list">
          <li>
            <p>
              <Trans
                i18nKey="components.claimsLeaveSpansBenefitYears.bothCannotBeSubmittedNew"
                values={{
                  submittableDate: formatDate(
                    props.secondLeaveEarliestSubmissionDate
                  ).short(),
                }}
              />
            </p>
          </li>
        </ul>
        <p>
          {t(
            "components.claimsLeaveSpansBenefitYears.bothCannotBeSubmittedReminder"
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
};

export default LeaveSpansBenefitYearsMessage;
