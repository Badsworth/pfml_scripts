import Claim, {
  ClaimStatus,
  EmploymentStatus,
  LeaveReason,
  PaymentPreferenceMethod,
  ReasonQualifier,
} from "../../models/Claim";
import EmployerBenefit, {
  EmployerBenefitType,
} from "../../models/EmployerBenefit";
import OtherIncome, { OtherIncomeType } from "../../models/OtherIncome";
import Step, { ClaimSteps } from "../../models/Step";
import { compact, get } from "lodash";
import BackButton from "../../components/BackButton";
import Button from "../../components/Button";
import { DateTime } from "luxon";
import Heading from "../../components/Heading";
import PreviousLeave from "../../models/PreviousLeave";
import PropTypes from "prop-types";
import React from "react";
import ReviewHeading from "../../components/ReviewHeading";
import ReviewRow from "../../components/ReviewRow";
import Title from "../../components/Title";
import claimantConfigs from "../../flows/claimant";
import findKeyByValue from "../../utils/findKeyByValue";
import formatDateRange from "../../utils/formatDateRange";
import { isFeatureEnabled } from "../../services/featureFlags";
import useThrottledHandler from "../../hooks/useThrottledHandler";
import { useTranslation } from "../../locales/i18n";
import withClaim from "../../hoc/withClaim";

/**
 * Format an address onto a single line, or return undefined if the address
 * is empty.
 */
function formatAddress(address) {
  let formatted = compact([
    get(address, "line_1"),
    get(address, "line_2"),
    get(address, "city"),
    get(address, "state"),
  ]).join(", ");

  const zip = get(address, "zip");
  if (zip) formatted += " " + zip;

  return formatted;
}

/**
 * Application review page, allowing a user to review the info
 * they've entered before they submit it.
 */
export const Review = (props) => {
  const { t } = useTranslation();
  const { appLogic, claim } = props;

  const paymentPreference = get(claim, "temp.payment_preferences[0]");
  const reason = get(claim, "leave_details.reason");
  const reasonQualifier = get(claim, "leave_details.reason_qualifier");

  const steps = Step.createClaimStepsFromMachine(
    claimantConfigs,
    { claim: props.claim },
    null
  );

  const getStepEditHref = (name) => {
    const step = steps.find((s) => s.name === name);

    if (step && step.editable) return step.href;
  };

  const handleSubmit = useThrottledHandler(() =>
    appLogic.claims.submit(claim.application_id)
  );

  const usePartOneReview =
    isFeatureEnabled("enableProgressiveApp") &&
    claim.status !== ClaimStatus.submitted;

  // Adjust heading levels depending on if there's a "Part 1" heading at the top of the page or not
  const reviewHeadingLevel = usePartOneReview ? "3" : "2";
  const reviewRowLevel = usePartOneReview ? "4" : "3";

  return (
    <div className="measure-6">
      <BackButton />

      {usePartOneReview ? (
        <React.Fragment>
          <Title hidden>{t("pages.claimsReview.titlePartOneReview")}</Title>

          <Heading className="margin-top-0" level="2" size="1">
            {/* This heading has two lines which are each styled differently */}
            <span className="display-block font-heading-2xs margin-bottom-2 text-base-dark text-bold">
              {t("pages.claimsReview.partHeading")}
            </span>
            {t("pages.claimsReview.pageHeading")}
          </Heading>
        </React.Fragment>
      ) : (
        <Title>{t("pages.claimsReview.titleFinalReview")}</Title>
      )}

      {/* EMPLOYEE IDENTITY */}
      <ReviewHeading
        editHref={getStepEditHref(ClaimSteps.verifyId)}
        editText={t("pages.claimsReview.editLink")}
        level={reviewHeadingLevel}
      >
        {t("pages.claimsReview.verifyIdSectionHeading")}
      </ReviewHeading>

      <ReviewRow
        level={reviewRowLevel}
        label={t("pages.claimsReview.userNameLabel")}
      >
        {[
          get(claim, "first_name"),
          get(claim, "middle_name"),
          get(claim, "last_name"),
        ].join(" ")}
      </ReviewRow>

      <ReviewRow
        level={reviewRowLevel}
        label={t("pages.claimsReview.residentialAddressLabel")}
      >
        {formatAddress(get(claim, "residential_address"))}
      </ReviewRow>

      {claim.has_state_id && (
        <ReviewRow
          level={reviewRowLevel}
          label={t("pages.claimsReview.userStateIdLabel")}
        >
          {claim.mass_id}
        </ReviewRow>
      )}

      {/* TODO (CP-891): Use the API response for the PII fields */}
      <ReviewRow
        level={reviewRowLevel}
        label={t("pages.claimsReview.userSsnLabel")}
      >
        {get(claim, "tax_identifier")}
      </ReviewRow>
      {/* TODO (CP-891): Use the API response for the PII fields */}
      <ReviewRow
        level={reviewRowLevel}
        label={t("pages.claimsReview.userDateOfBirthLabel")}
      >
        **/**/****
      </ReviewRow>

      {/* LEAVE DETAILS */}
      <ReviewHeading
        editHref={getStepEditHref(ClaimSteps.leaveDetails)}
        editText={t("pages.claimsReview.editLink")}
        level={reviewHeadingLevel}
      >
        {t("pages.claimsReview.leaveDetailsSectionHeading")}
      </ReviewHeading>

      <ReviewRow
        level={reviewRowLevel}
        label={t("pages.claimsReview.leaveReasonLabel")}
      >
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
            level={reviewRowLevel}
            label={t("pages.claimsReview.pregnancyOrRecentBirthLabel")}
          >
            {get(claim, "leave_details.pregnant_or_recent_birth") === true
              ? t("pages.claimsReview.pregnancyChoiceYes")
              : t("pages.claimsReview.pregnancyChoiceNo")}
          </ReviewRow>
        </React.Fragment>
      )}

      {reason === LeaveReason.bonding &&
        reasonQualifier === ReasonQualifier.newBorn && (
          <React.Fragment>
            {/* TODO (POL-99): determine if date of placement is PII, if so need to adhere to CP-891 */}
            <ReviewRow
              level={reviewRowLevel}
              label={t("pages.claimsReview.childBirthDateLabel")}
            >
              **/**/****
            </ReviewRow>
          </React.Fragment>
        )}

      {reason === LeaveReason.bonding &&
        (reasonQualifier === ReasonQualifier.adoption ||
          reasonQualifier === ReasonQualifier.fosterCare) && (
          <React.Fragment>
            {/* TODO (POL-99): determine if date of placement is PII if so need to adhere to CP-891 */}
            <ReviewRow
              level={reviewRowLevel}
              label={t("pages.claimsReview.childPlacementDateLabel")}
            >
              **/**/****
            </ReviewRow>
          </React.Fragment>
        )}

      <ReviewRow
        level={reviewRowLevel}
        label={t("pages.claimsReview.leaveDurationLabel")}
      >
        {formatDateRange(
          get(claim, "temp.leave_details.start_date"),
          get(claim, "temp.leave_details.end_date")
        )}
      </ReviewRow>

      <ReviewRow
        level={reviewRowLevel}
        label={t("pages.claimsReview.leaveDurationTypeLabel")}
      >
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
        <ReviewRow
          level={reviewRowLevel}
          label={t("pages.claimsReview.averageWorkHoursLabel")}
        >
          {get(claim, "temp.leave_details.avg_weekly_work_hours")}
        </ReviewRow>
      )}

      {/* EMPLOYMENT INFO */}
      <ReviewHeading
        editHref={getStepEditHref(ClaimSteps.employerInformation)}
        editText={t("pages.claimsReview.editLink")}
        level={reviewHeadingLevel}
      >
        {t("pages.claimsReview.employmentSectionHeading")}
      </ReviewHeading>

      {get(claim, "employment_status") && (
        <ReviewRow
          level={reviewRowLevel}
          label={t("pages.claimsReview.employmentStatusLabel")}
        >
          {t("pages.claimsReview.employmentStatusValue", {
            context: findKeyByValue(
              EmploymentStatus,
              get(claim, "employment_status")
            ),
          })}
        </ReviewRow>
      )}

      {get(claim, "employment_status") === EmploymentStatus.employed && ( // only display this if the claimant is Employed
        <ReviewRow
          level={reviewRowLevel}
          label={t("pages.claimsReview.employerFeinLabel")}
        >
          {get(claim, "employer_fein")}
        </ReviewRow>
      )}

      {get(claim, "employment_status") === EmploymentStatus.employed && ( // only display this if the claimant is Employed
        <ReviewRow
          level={reviewRowLevel}
          label={t("pages.claimsReview.employerNotifiedLabel")}
        >
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
        editHref={getStepEditHref(ClaimSteps.otherLeave)}
        editText={t("pages.claimsReview.editLink")}
        level={reviewHeadingLevel}
      >
        {t("pages.claimsReview.otherLeaveSectionHeading")}
      </ReviewHeading>

      <ReviewRow
        level={reviewRowLevel}
        label={t("pages.claimsReview.employerBenefitLabel")}
      >
        {get(claim, "has_employer_benefits") === true
          ? t("pages.claimsReview.otherLeaveChoiceYes")
          : t("pages.claimsReview.otherLeaveChoiceNo")}
      </ReviewRow>

      {get(claim, "has_employer_benefits") && (
        <EmployerBenefitList
          entries={get(claim, "employer_benefits")}
          reviewRowLevel={reviewRowLevel}
        />
      )}

      <ReviewRow
        level={reviewRowLevel}
        label={t("pages.claimsReview.otherIncomeLabel")}
      >
        {get(claim, "has_other_incomes") === true
          ? t("pages.claimsReview.otherLeaveChoiceYes")
          : t("pages.claimsReview.otherLeaveChoiceNo")}
      </ReviewRow>

      {get(claim, "has_other_incomes") && (
        <OtherIncomeList
          entries={get(claim, "other_incomes")}
          reviewRowLevel={reviewRowLevel}
        />
      )}

      <ReviewRow
        level={reviewRowLevel}
        label={t("pages.claimsReview.previousLeaveLabel")}
        editText={t("pages.claimsReview.editLink")}
      >
        {get(claim, "has_previous_leaves") === true
          ? t("pages.claimsReview.otherLeaveChoiceYes")
          : t("pages.claimsReview.otherLeaveChoiceNo")}
      </ReviewRow>

      {get(claim, "has_previous_leaves") && (
        <PreviousLeaveList
          entries={get(claim, "previous_leaves")}
          reviewRowLevel={reviewRowLevel}
        />
      )}

      {usePartOneReview ? (
        <React.Fragment>
          <p className="margin-top-9">
            {t("pages.claimsReview.partOneNextStepsLine1")}
          </p>
          <p>{t("pages.claimsReview.partOneNextStepsLine2")}</p>
          <p>{t("pages.claimsReview.partOneNextStepsLine3")}</p>
        </React.Fragment>
      ) : (
        <React.Fragment>
          {/* PAYMENT METHOD */}
          <ReviewHeading
            editHref={getStepEditHref(ClaimSteps.payment)}
            editText={t("pages.claimsReview.editLink")}
            level={reviewHeadingLevel}
          >
            {t("pages.claimsReview.paymentSectionHeading")}
          </ReviewHeading>

          {paymentPreference.payment_method && (
            <ReviewRow
              label={t("pages.claimsReview.paymentMethodLabel")}
              level={reviewRowLevel}
            >
              {t("pages.claimsReview.paymentMethodValue", {
                context: findKeyByValue(
                  PaymentPreferenceMethod,
                  paymentPreference.payment_method
                ),
              })}
            </ReviewRow>
          )}
        </React.Fragment>
      )}

      <Button
        className="margin-top-3"
        onClick={handleSubmit}
        type="button"
        loading={handleSubmit.isThrottled}
      >
        {t("pages.claimsReview.submitAction", {
          context: usePartOneReview ? "part1" : "final",
        })}
      </Button>
    </div>
  );
};

Review.propTypes = {
  appLogic: PropTypes.object.isRequired,
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
  const { entries, reviewRowLevel } = props;

  return entries.map((entry, index) => {
    const label = t("pages.claimsReview.employerBenefitEntryLabel", {
      count: index + 1,
    });
    // TODO (CP-567): remove this ternary operator once we begin saving other leave to
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
        reviewRowLevel={reviewRowLevel}
      />
    );
  });
};

EmployerBenefitList.propTypes = {
  entries: PropTypes.arrayOf(PropTypes.instanceOf(EmployerBenefit)).isRequired,
  reviewRowLevel: PropTypes.oneOf(["2", "3", "4", "5", "6"]).isRequired,
};

/*
 * Helper component for rendering an array of OtherIncome
 * objects.
 */
export const OtherIncomeList = (props) => {
  const { t } = useTranslation();
  const { entries, reviewRowLevel } = props;

  return entries.map((entry, index) => {
    const label = t("pages.claimsReview.otherIncomeEntryLabel", {
      count: index + 1,
    });
    // TODO (CP-567): remove this ternary operator once we begin saving other leave to
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
        reviewRowLevel={reviewRowLevel}
      />
    );
  });
};

OtherIncomeList.propTypes = {
  entries: PropTypes.arrayOf(PropTypes.instanceOf(OtherIncome)).isRequired,
  reviewRowLevel: PropTypes.oneOf(["2", "3", "4", "5", "6"]).isRequired,
};

/*
 * Helper component for rendering an array of PreviousLeave
 * objects.
 */
export const PreviousLeaveList = (props) => {
  const { t } = useTranslation();
  const { entries, reviewRowLevel } = props;

  return entries.map((entry, index) => {
    const label = t("pages.claimsReview.previousLeaveEntryLabel", {
      count: index + 1,
    });
    const dates = formatDateRange(entry.leave_start_date, entry.leave_end_date);

    return (
      <OtherLeaveEntry
        key={index}
        label={label}
        dates={dates}
        reviewRowLevel={reviewRowLevel}
      />
    );
  });
};

PreviousLeaveList.propTypes = {
  entries: PropTypes.arrayOf(PropTypes.instanceOf(PreviousLeave)).isRequired,
  reviewRowLevel: PropTypes.oneOf(["2", "3", "4", "5", "6"]).isRequired,
};

/*
 * Helper component for rendering a single other leave entry. This will
 * render a ReviewRow with the specified label, date string,
 * and an optional type string and amount string
 */
export const OtherLeaveEntry = (props) => {
  const { amount, dates, label, reviewRowLevel, type } = props;

  return (
    <ReviewRow level={reviewRowLevel} label={label}>
      {type && (
        <React.Fragment>
          {type}
          <br />
        </React.Fragment>
      )}
      {/* TODO (CP-567): once we're saving other leave to the api then we can remove
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
  reviewRowLevel: PropTypes.oneOf(["2", "3", "4", "5", "6"]).isRequired,
  type: PropTypes.string,
};

export default withClaim(Review);
