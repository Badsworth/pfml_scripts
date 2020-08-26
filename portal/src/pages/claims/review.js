import Claim, {
  EmploymentStatus,
  LeaveReason,
  PaymentPreferenceMethod,
} from "../../models/Claim";
import EmployerBenefit, {
  EmployerBenefitType,
} from "../../models/EmployerBenefit";
import OtherIncome, { OtherIncomeType } from "../../models/OtherIncome";
import Step, { ClaimSteps } from "../../models/Step";
import { compact, get } from "lodash";
import routeWithParams, {
  createRouteWithQuery,
} from "../../utils/routeWithParams";
import BackButton from "../../components/BackButton";
import ButtonLink from "../../components/ButtonLink";
import { DateTime } from "luxon";
import PreviousLeave from "../../models/PreviousLeave";
import PropTypes from "prop-types";
import React from "react";
import ReviewHeading from "../../components/ReviewHeading";
import ReviewRow from "../../components/ReviewRow";
import Title from "../../components/Title";
import claimantConfigs from "../../flows/claimant";
import findKeyByValue from "../../utils/findKeyByValue";
import formatDateRange from "../../utils/formatDateRange";
import { useTranslation } from "../../locales/i18n";
import withClaim from "../../hoc/withClaim";

/**
 * Application review page, allowing a user to review the info
 * they've entered before they submit it.
 */
const Review = (props) => {
  const { t } = useTranslation();
  const { claim } = props;

  const paymentPreference = get(claim, "temp.payment_preferences[0]");
  const reason = get(claim, "leave_details.reason");

  const steps = Step.createClaimStepsFromMachine(
    claimantConfigs,
    { claim: props.claim },
    null
  );

  const routeForStep = (name) => {
    const step = steps.find((s) => s.name === name);

    if (step) return createRouteWithQuery(step.initialPage, props.query);
  };

  return (
    <div className="measure-6">
      <BackButton />
      <Title>{t("pages.claimsReview.title")}</Title>

      {/* EMPLOYEE IDENTITY */}
      <ReviewHeading
        editHref={routeForStep(ClaimSteps.verifyId)}
        editText={t("pages.claimsReview.editLink")}
      >
        {t("pages.claimsReview.userSectionHeading")}
      </ReviewHeading>

      <ReviewRow label={t("pages.claimsReview.userNameLabel")}>
        {[
          get(claim, "first_name"),
          get(claim, "middle_name"),
          get(claim, "last_name"),
        ].join(" ")}
      </ReviewRow>

      <ReviewRow label={t("pages.claimsReview.residentialAddressLabel")}>
        {compact([
          get(claim, "temp.residential_address.line_1"),
          get(claim, "temp.residential_address.line_2"),
          get(claim, "temp.residential_address.city"),
          get(claim, "temp.residential_address.state"),
        ]).join(", ")}{" "}
        {get(claim, "temp.residential_address.zip")}
      </ReviewRow>

      {/* TODO: Use the API response for the PII fields */}
      <ReviewRow label={t("pages.claimsReview.userDateOfBirthLabel")}>
        **/**/****
      </ReviewRow>
      <ReviewRow label={t("pages.claimsReview.userSsnLabel")}>
        *********
      </ReviewRow>

      {claim.has_state_id && (
        <ReviewRow label={t("pages.claimsReview.userStateIdLabel")}>
          {claim.mass_id}
        </ReviewRow>
      )}

      {/* LEAVE DETAILS */}
      <ReviewHeading
        editHref={routeForStep(ClaimSteps.leaveDetails)}
        editText={t("pages.claimsReview.editLink")}
      >
        {t("pages.claimsReview.leaveSectionHeading")}
      </ReviewHeading>
      <ReviewRow label={t("pages.claimsReview.leaveReasonLabel")}>
        {t("pages.claimsReview.leaveReasonValue", {
          context: findKeyByValue(
            LeaveReason,
            get(claim, "leave_details.reason")
          ),
        })}
      </ReviewRow>
      {reason === LeaveReason.medical && (
        <React.Fragment>
          <ReviewRow
            label={t("pages.claimsReview.pregnancyOrRecentBirthLabel")}
          >
            {get(claim, "pregnant_or_recent_birth") === true
              ? t("pages.claimsReview.pregnancyChoiceYes")
              : t("pages.claimsReview.pregnancyChoiceNo")}
          </ReviewRow>
        </React.Fragment>
      )}
      {reason === LeaveReason.bonding && (
        <React.Fragment>
          {/* TODO: Use the API response for the PII fields */}
          <ReviewRow label={t("pages.claimsReview.bondingLeaveLabel")}>
            **/**/****
          </ReviewRow>
        </React.Fragment>
      )}

      <ReviewRow label={t("pages.claimsReview.leaveDurationLabel")}>
        {formatDateRange(
          get(claim, "temp.leave_details.start_date"),
          get(claim, "temp.leave_details.end_date")
        )}
      </ReviewRow>

      <ReviewRow label={t("pages.claimsReview.leaveDurationTypeLabel")}>
        {compact([
          claim.isContinuous
            ? t("pages.claimsReview.leaveDurationTypeContinuous")
            : null,
          claim.isReducedSchedule
            ? t("pages.claimsReview.leaveDurationTypeReducedSchedule")
            : null,
          claim.isIntermittent
            ? t("pages.claimsReview.leaveDurationTypeIntermittent")
            : null,
        ]).join(", ")}
      </ReviewRow>

      {get(claim, "temp.leave_details.avg_weekly_work_hours") && (
        <ReviewRow label={t("pages.claimsReview.averageWorkHoursLabel")}>
          {get(claim, "temp.leave_details.avg_weekly_work_hours")}
        </ReviewRow>
      )}

      {/* EMPLOYMENT INFO */}
      <ReviewHeading
        editHref={routeForStep(ClaimSteps.employerInformation)}
        editText={t("pages.claimsReview.editLink")}
      >
        {t("pages.claimsReview.employmentSectionHeading")}
      </ReviewHeading>

      {get(claim, "employment_status") && (
        <ReviewRow label={t("pages.claimsReview.employmentStatusLabel")}>
          {t("pages.claimsReview.employmentStatusValue", {
            context: findKeyByValue(
              EmploymentStatus,
              get(claim, "employment_status")
            ),
          })}
        </ReviewRow>
      )}

      {get(claim, "employment_status") === EmploymentStatus.employed && ( // only display this if the claimant is Employed
        <ReviewRow label={t("pages.claimsReview.employerFeinLabel")}>
          {get(claim, "employer_fein")}
        </ReviewRow>
      )}

      {get(claim, "employment_status") === EmploymentStatus.employed && ( // only display this if the claimant is Employed
        <ReviewRow label={t("pages.claimsReview.employerNotifiedLabel")}>
          {t("pages.claimsReview.employerNotifiedValue", {
            context: (!!get(
              claim,
              "leave_details.employer_notified"
            )).toString(),
            date: DateTime.fromISO(
              get(claim, "leave_details.employer_notification_date")
            ).toLocaleString(),
          })}
        </ReviewRow>
      )}

      {/* OTHER LEAVE */}
      <ReviewHeading
        editHref={routeForStep(ClaimSteps.otherLeave)}
        editText={t("pages.claimsReview.editLink")}
      >
        {t("pages.claimsReview.otherLeaveSectionHeading")}
      </ReviewHeading>

      <ReviewRow label={t("pages.claimsReview.employerBenefitLabel")}>
        {get(claim, "has_employer_benefits") === true
          ? t("pages.claimsReview.otherLeaveChoiceYes")
          : t("pages.claimsReview.otherLeaveChoiceNo")}
      </ReviewRow>

      {get(claim, "has_employer_benefits") && (
        <EmployerBenefitList entries={get(claim, "employer_benefits")} />
      )}

      <ReviewRow label={t("pages.claimsReview.otherIncomeLabel")}>
        {get(claim, "has_other_incomes") === true
          ? t("pages.claimsReview.otherLeaveChoiceYes")
          : t("pages.claimsReview.otherLeaveChoiceNo")}
      </ReviewRow>

      {get(claim, "has_other_incomes") && (
        <OtherIncomeList entries={get(claim, "other_incomes")} />
      )}

      <ReviewRow
        label={t("pages.claimsReview.previousLeaveLabel")}
        editText={t("pages.claimsReview.editLink")}
      >
        {get(claim, "has_previous_leaves") === true
          ? t("pages.claimsReview.otherLeaveChoiceYes")
          : t("pages.claimsReview.otherLeaveChoiceNo")}
      </ReviewRow>

      {get(claim, "has_previous_leaves") && (
        <PreviousLeaveList entries={get(claim, "previous_leaves")} />
      )}

      {/* PAYMENT METHOD */}
      <ReviewHeading
        editHref={routeForStep(ClaimSteps.payment)}
        editText={t("pages.claimsReview.editLink")}
      >
        {t("pages.claimsReview.paymentSectionHeading")}
      </ReviewHeading>

      {paymentPreference.payment_method && (
        <ReviewRow label={t("pages.claimsReview.paymentMethodLabel")}>
          {t("pages.claimsReview.paymentMethodValue", {
            context: findKeyByValue(
              PaymentPreferenceMethod,
              paymentPreference.payment_method
            ),
          })}
        </ReviewRow>
      )}

      <ButtonLink
        className="margin-top-3"
        href={routeWithParams("claims.confirm", props.query)}
      >
        {t("pages.claimsReview.confirmationAction")}
      </ButtonLink>
    </div>
  );
};

Review.propTypes = {
  claim: PropTypes.instanceOf(Claim),
  query: PropTypes.shape({
    claim_id: PropTypes.string,
  }),
};

/*
 * Helper component for rendering an array of EmployerBenefit
 * objects.
 */
export const EmployerBenefitList = (props) => {
  const { t } = useTranslation();
  const entries = props.entries;

  return entries.map((entry, index) => {
    const label = t("pages.claimsReview.employerBenefitEntryLabel", {
      count: index + 1,
    });
    // TODO: CP-567 remove this ternary operator once we begin saving other leave to
    // the API. We'll always have a type then
    const type = entry.benefit_type
      ? t("pages.claimsReview.employerBenefitType", {
          context: findKeyByValue(EmployerBenefitType, entry.benefit_type),
        })
      : null;
    const dates = formatDateRange(
      entry.benefit_start_date,
      entry.benefit_end_date
    );
    const amount =
      entry.benefit_amount_dollars &&
      t("pages.claimsReview.otherLeaveDollarAmount", {
        amount: entry.benefit_amount_dollars,
      });

    return (
      <OtherLeaveEntry
        key={index}
        label={label}
        type={type}
        dates={dates}
        amount={amount}
      />
    );
  });
};

EmployerBenefitList.propTypes = {
  entries: PropTypes.arrayOf(PropTypes.instanceOf(EmployerBenefit)).isRequired,
};

/*
 * Helper component for rendering an array of OtherIncome
 * objects.
 */
export const OtherIncomeList = (props) => {
  const { t } = useTranslation();
  const entries = props.entries;

  return entries.map((entry, index) => {
    const label = t("pages.claimsReview.otherIncomeEntryLabel", {
      count: index + 1,
    });
    // TODO: CP-567 remove this ternary operator once we begin saving other leave to
    // the API. We'll always have a type then
    const type = entry.income_type
      ? t("pages.claimsReview.otherIncomeType", {
          context: findKeyByValue(OtherIncomeType, entry.income_type),
        })
      : null;
    const dates = formatDateRange(
      entry.income_start_date,
      entry.income_end_date
    );
    const amount =
      entry.income_amount_dollars &&
      t("pages.claimsReview.otherLeaveDollarAmount", {
        amount: entry.income_amount_dollars,
      });

    return (
      <OtherLeaveEntry
        key={index}
        label={label}
        type={type}
        dates={dates}
        amount={amount}
      />
    );
  });
};

OtherIncomeList.propTypes = {
  entries: PropTypes.arrayOf(PropTypes.instanceOf(OtherIncome)).isRequired,
};

/*
 * Helper component for rendering an array of PreviousLeave
 * objects.
 */
export const PreviousLeaveList = (props) => {
  const { t } = useTranslation();
  const entries = props.entries;

  return entries.map((entry, index) => {
    const label = t("pages.claimsReview.previousLeaveEntryLabel", {
      count: index + 1,
    });
    const dates = formatDateRange(entry.leave_start_date, entry.leave_end_date);

    return <OtherLeaveEntry key={index} label={label} dates={dates} />;
  });
};

PreviousLeaveList.propTypes = {
  entries: PropTypes.arrayOf(PropTypes.instanceOf(PreviousLeave)).isRequired,
};

/*
 * Helper component for rendering a single other leave entry. This will
 * render a ReviewRow with the specified label, date string,
 * and an optional type string and amount string
 */
export const OtherLeaveEntry = (props) => {
  const { label, type, dates, amount } = props;

  return (
    <ReviewRow label={label}>
      {type && (
        <React.Fragment>
          {type}
          <br />
        </React.Fragment>
      )}
      {/* TODO: CP-567 once we're saving other leave to the api then we can remove
          the conditional rendering here and instead always render the date string */}
      {dates && (
        <React.Fragment>
          {dates}
          <br />
        </React.Fragment>
      )}
      {amount}
    </ReviewRow>
  );
};

OtherLeaveEntry.propTypes = {
  amount: PropTypes.string,
  dates: PropTypes.string.isRequired,
  label: PropTypes.string.isRequired,
  type: PropTypes.string,
};

export default withClaim(Review);
