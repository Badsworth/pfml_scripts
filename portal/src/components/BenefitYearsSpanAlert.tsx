import Alert from "./core/Alert";
import ApplicationSplit from "src/models/ApplicationSplit";
import React from "react";
import { Trans } from "react-i18next";
import dayjs from "dayjs";
import formatDate from "../utils/formatDate";
import { isFeatureEnabled } from "src/services/featureFlags";
import routes from "../routes";

interface BenefitYearsSpanAlertProps {
  computed_application_split: ApplicationSplit | null;
}

/**
 * Alert component shared across multiple pages for displaying
 * a claimant's leave dates that crosses benefit years
 */
function BenefitYearsSpanAlert(props: BenefitYearsSpanAlertProps) {
  const { computed_application_split } = props;

  const number_of_calendar_days_ahead = 60;

  const getIntroduction = () => {
    return (
      <Trans
        i18nKey="pages.claimsReview.leaveDetailsBenefitYearsIntroduction"
        values={{
          startDate: formatDate(
            computed_application_split?.crossed_benefit_year
              .benefit_year_start_date
          ).short(),
          endDate: formatDate(
            computed_application_split?.crossed_benefit_year
              .benefit_year_end_date
          ).short(),
        }}
        components={{
          "benefit-year-guide-link": (
            <a
              href={routes.external.massgov.benefitsGuide_benefitYears}
              rel="noopener noreferrer"
              target="_blank"
            />
          ),
        }}
      />
    );
  };

  const getCurrentBenefitYear = () => {
    return (
      <Trans
        i18nKey="pages.claimsReview.leaveDetailsCurrentBenefitYearsDates"
        values={{
          startDate: formatDate(
            computed_application_split?.application_dates_in_benefit_year
              .start_date
          ).short(),
          endDate: formatDate(
            computed_application_split?.application_dates_in_benefit_year
              .end_date
          ).short(),
        }}
        components={{
          "benefit-year-guide-link": (
            <a
              href={routes.external.massgov.benefitsGuide_benefitYears}
              rel="noopener noreferrer"
              target="_blank"
            />
          ),
        }}
      />
    );
  };

  const getNewBenefitYear = () => {
    return (
      <Trans
        i18nKey="pages.claimsReview.leaveDetailsNewBenefitYearsDates"
        values={{
          startDate: formatDate(
            computed_application_split?.application_dates_outside_benefit_year
              .start_date
          ).short(),
          endDate: formatDate(
            computed_application_split?.application_dates_outside_benefit_year
              .end_date
          ).short(),
        }}
        components={{
          "benefit-year-guide-link": (
            <a
              href={routes.external.massgov.benefitsGuide_benefitYears}
              rel="noopener noreferrer"
              target="_blank"
            />
          ),
        }}
      />
    );
  };

  if (isFeatureEnabled("splitClaimsAcrossBY") && computed_application_split) {
    // The first option should be displayed when the start date of leave in the new benefit year is less than or equal to 60 calendar days in the future
    const sixy_days_ahead = dayjs().add(number_of_calendar_days_ahead, "day");
    if (
      dayjs(
        computed_application_split.application_dates_in_benefit_year.start_date
      ).isBefore(sixy_days_ahead)
    ) {
      return (
        <Alert
          heading="Your leave dates extend into a new benefit year."
          headingSize="2"
          role="alert"
          state="info"
        >
          <p>{getIntroduction()}</p>

          <ul>
            <li>{getCurrentBenefitYear()}</li>
            <li>{getNewBenefitYear()}</li>
          </ul>

          <p>We’ll review each application separately. This means that:</p>

          <ul>
            <li>
              The Department's determination for one application may be
              different from its determination for the other.
            </li>
            <li>
              The Department will calculate your weekly benefit amount for each
              application separately. You may receive different payment amounts
              for each application. Learn more about{" "}
              <a href="#">how PFML weekly benefit amounts are calculated.</a>
            </li>
            <li>
              You'll have two 7-day waiting periods, one at the start of each
              period of your leave. Learn more about the{" "}
              <a href="#">7-day waiting period.</a>
            </li>
          </ul>
        </Alert>
      );
    } else if (
      dayjs(
        computed_application_split.application_dates_outside_benefit_year
          .start_date
      ).isAfter(sixy_days_ahead)
    ) {
      // The second option should be used when the start date of leave in the new benefit year is more than 60 calendar days in the future:
      <Alert
        heading="Your leave dates extend into a new benefit year."
        headingSize="2"
        role="alert"
        state="info"
      >
        <p>{getIntroduction()}</p>

        <p>{getCurrentBenefitYear()}</p>

        <ul>
          <li>
            Your in-progress application will be viewable by our Contact Center
            staff. If you need to make edits to Part 1, you’ll need to call our
            Contact Center at (833) 344‑7365.
          </li>
          <li>
            We’ll also notify your employer that you’ve started an application
            for paid family and medical leave.
          </li>
          <li>
            Next, you’ll be able to work on Parts 2 and 3, and submit your
            application.
          </li>
        </ul>

        <p>{getNewBenefitYear()}</p>

        <ul>
          <li>
            You will be able to submit Part 1 of your new benefit year
            application on 3/2/2022. This is 60 days before the start of your
            leave in the new benefit year.
          </li>
        </ul>
      </Alert>;
    } else if (
      dayjs(
        computed_application_split.application_dates_in_benefit_year.start_date
      ).isBefore(sixy_days_ahead) &&
      dayjs(
        computed_application_split.application_dates_outside_benefit_year
          .start_date
      ).isAfter(sixy_days_ahead)
    ) {
      // The third option is if both leave start dates are >60 days out:
      // The second option should be used when the start date of leave in the new benefit year is more than 60 calendar days in the future:
      <Alert
        heading="Your leave dates extend into a new benefit year."
        headingSize="2"
        role="alert"
        state="info"
      >
        <p>{getIntroduction()}</p>

        <p>{getCurrentBenefitYear()}</p>

        <ul>
          <li>
            You will be able to submit Part 1 of your current benefit year
            application on [MM/DD/YYYY]. This is 60 days before the start of
            your leave in the current benefit year.
          </li>
        </ul>

        <p>{getNewBenefitYear()}</p>

        <ul>
          <li>
            You will be able to submit Part 1 of your new benefit year
            application on [MM/DD/YYYY]. This is 60 days before the start of
            your leave in the new benefit year.
          </li>
        </ul>

        <p>
          Applications cannot be submitted earlier than 60 days before the start
          of leave."
        </p>
      </Alert>;
    }
  }

  return (
    <Alert
      heading="Your leave dates extend into a new benefit year."
      headingSize="2"
      role="alert"
      state="info"
    >
      <p>{getIntroduction()}</p>

      <ul>
        <li>{getCurrentBenefitYear()}</li>
        <li>{getNewBenefitYear()}</li>
      </ul>

      <p>We’ll review each application separately. This means that:</p>

      <ul>
        <li>
          The Department's determination for one application may be different
          from its determination for the other.
        </li>
        <li>
          The Department will calculate your weekly benefit amount for each
          application separately. You may receive different payment amounts for
          each application. Learn more about{" "}
          <a href="#">how PFML weekly benefit amounts are calculated.</a>
        </li>
        <li>
          You'll have two 7-day waiting periods, one at the start of each period
          of your leave. Learn more about the{" "}
          <a href="#">7-day waiting period.</a>
        </li>
      </ul>
    </Alert>
  );
}

export default BenefitYearsSpanAlert;
