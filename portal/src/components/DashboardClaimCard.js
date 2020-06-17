import ButtonLink from "../components/ButtonLink";
import Claim from "../models/Claim";
import Heading from "../components/Heading";
import PropTypes from "prop-types";
import React from "react";
import routeWithParams from "../utils/routeWithParams";
import { useTranslation } from "../locales/i18n";

/**
 * Item displayed in the "Active claims" section of the dashboard, for
 * an individual in progress claim
 */
function DashboardClaimCard(props) {
  const { claim, number } = props;
  const { t } = useTranslation();

  return (
    <article className="maxw-mobile-lg border border-base-lighter margin-bottom-3 padding-3">
      <span className="usa-tag bg-primary-lighter display-inline-block margin-bottom-1 text-bold text-primary text-no-uppercase">
        {t("pages.index.tagInProgress")}
      </span>
      <Heading className="margin-top-05 margin-bottom-2" level="3">
        {t("pages.index.claimCardHeading", { number })}
      </Heading>

      <ButtonLink
        className="margin-top-1"
        href={routeWithParams("claims.checklist", {
          claim_id: claim.application_id,
        })}
      >
        {t("pages.index.resumeClaimButton")}
      </ButtonLink>
    </article>
  );
}

DashboardClaimCard.propTypes = {
  claim: PropTypes.instanceOf(Claim),
  /**
   * Cards are displayed in a list. What position is this card?
   */
  number: PropTypes.number.isRequired,
};

export default DashboardClaimCard;
