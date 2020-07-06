import Claim, { EmploymentStatus, LeaveReason } from "../../models/Claim";
import routeWithParams, {
  createRouteWithQuery,
} from "../../utils/routeWithParams";
import BackButton from "../../components/BackButton";
import ButtonLink from "../../components/ButtonLink";
import { DateTime } from "luxon";
import PropTypes from "prop-types";
import React from "react";
import ReviewHeading from "../../components/ReviewHeading";
import ReviewRow from "../../components/ReviewRow";
import Title from "../../components/Title";
import User from "../../models/User";
import findKeyByValue from "../../utils/findKeyByValue";
import formatDateRange from "../../utils/formatDateRange";
import get from "lodash/get";
import { stepDefinitions } from "../../flows/leave-application";
import { useTranslation } from "../../locales/i18n";
import withClaim from "../../hoc/withClaim";

/**
 * Application review page, allowing a user to review the info
 * they've entered before they submit it.
 */
export const Review = (props) => {
  const { t } = useTranslation();
  const { claim, user } = props;

  const reason = get(claim, "leave_details.reason");

  const routeForStepDefinition = (name) => {
    const stepDefinition = stepDefinitions.find((s) => s.name === name);

    if (stepDefinition && stepDefinition.pages.length)
      return createRouteWithQuery(stepDefinition.pages[0].route, props.query);
  };

  return (
    <div className="measure-6">
      <BackButton />
      <Title>{t("pages.claimsReview.title")}</Title>

      {/* EMPLOYEE IDENTITY */}
      <ReviewHeading
        editHref={routeForStepDefinition("verifyId")}
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

      {/* TODO: Use the API response for the PII fields */}
      <ReviewRow label={t("pages.claimsReview.userDateOfBirthLabel")}>
        **/**/****
      </ReviewRow>
      <ReviewRow label={t("pages.claimsReview.userSsnLabel")}>
        *********
      </ReviewRow>

      {user.has_state_id && (
        <ReviewRow label={t("pages.claimsReview.userStateIdLabel")}>
          *********
        </ReviewRow>
      )}

      {/* LEAVE DETAILS */}
      <ReviewHeading
        editHref={routeForStepDefinition("leaveDetails")}
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

      <ReviewRow label={t("pages.claimsReview.leaveDurationLabel")}>
        {formatDateRange(
          get(claim, "leave_details.continuous_leave_periods[0].start_date"),
          get(claim, "leave_details.continuous_leave_periods[0].end_date")
        )}
      </ReviewRow>
      <ReviewRow label={t("pages.claimsReview.leaveDurationTypeLabel")}>
        {t("pages.claimsReview.leaveDurationTypeValue", {
          context: get(claim, "duration_type"),
        })}
      </ReviewRow>

      {/* EMPLOYMENT INFO */}
      <ReviewHeading
        editHref={routeForStepDefinition("employerInformation")}
        editText={t("pages.claimsReview.editLink")}
      >
        {t("pages.claimsReview.employmentSectionHeading")}
      </ReviewHeading>

      {get(claim, "leave_details.employment_status") && (
        <ReviewRow label={t("pages.claimsReview.employmentStatusLabel")}>
          {t("pages.claimsReview.employmentStatusValue", {
            context: findKeyByValue(
              EmploymentStatus,
              get(claim, "leave_details.employment_status")
            ),
          })}
        </ReviewRow>
      )}

      {get(claim, "leave_details.employment_status") === // only display this if the claimant is Employed
        EmploymentStatus.employed && (
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
  user: PropTypes.instanceOf(User),
};

export default withClaim(Review);
