import BackButton from "../../components/BackButton";
import ButtonLink from "../../components/ButtonLink";
import Claim from "../../models/Claim";
import Heading from "../../components/Heading";
import PropTypes from "prop-types";
import React from "react";
import ReviewRow from "../../components/ReviewRow";
import Title from "../../components/Title";
import User from "../../models/User";
import formatDateRange from "../../utils/formatDateRange";
import get from "lodash/get";
import routeWithParams from "../../utils/routeWithParams";
import { useTranslation } from "../../locales/i18n";
import withClaim from "../../hoc/withClaim";

/**
 * Application review page, allowing a user to review the info
 * they've entered before they submit it.
 */
export const Review = (props) => {
  const { t } = useTranslation();
  const { claim, user } = props;

  return (
    <div className="measure-6">
      <BackButton />
      <Title>{t("pages.claimsReview.title")}</Title>

      {/* EMPLOYEE IDENTITY */}
      <Heading level="2">{t("pages.claimsReview.userSectionHeading")}</Heading>

      <ReviewRow heading={t("pages.claimsReview.userNameHeading")}>
        {[
          get(claim, "first_name"),
          get(claim, "middle_name"),
          get(claim, "last_name"),
        ].join(" ")}
      </ReviewRow>

      {/* TODO: Use the API response for the PII fields */}
      <ReviewRow heading={t("pages.claimsReview.userDateOfBirthHeading")}>
        **/**/****
      </ReviewRow>
      <ReviewRow heading={t("pages.claimsReview.userSsnHeading")}>
        *********
      </ReviewRow>

      {user.has_state_id && (
        <ReviewRow heading={t("pages.claimsReview.userStateIdHeading")}>
          *********
        </ReviewRow>
      )}

      {/* LEAVE DETAILS */}
      <Heading level="2">{t("pages.claimsReview.leaveSectionHeading")}</Heading>

      <ReviewRow heading={t("pages.claimsReview.leaveDurationHeading")}>
        {formatDateRange(
          get(claim, "leave_details.continuous_leave_periods[0].start_date"),
          get(claim, "leave_details.continuous_leave_periods[0].end_date")
        )}
      </ReviewRow>
      <ReviewRow heading={t("pages.claimsReview.leaveDurationTypeHeading")}>
        {t("pages.claimsReview.leaveDurationTypeValue", {
          context: get(claim, "duration_type"),
        })}
      </ReviewRow>

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
