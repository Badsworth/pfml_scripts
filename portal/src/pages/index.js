import React, { useEffect } from "react";
import Button from "../components/Button";
import DashboardClaimCard from "../components/DashboardClaimCard";
import Heading from "../components/Heading";
import PropTypes from "prop-types";
import Title from "../components/Title";
import User from "../models/User";
import routeWithParams from "../utils/routeWithParams";

import { useRouter } from "next/router";
import { useTranslation } from "../locales/i18n";

/**
 * "Dashboard" - Where a user is redirected to after successfully authenticating.
 */
const Index = ({ appLogic, user }) => {
  const { t } = useTranslation();
  const router = useRouter();

  const handleSubmit = async (event) => {
    event.preventDefault();

    const claim = await appLogic.createClaim();

    // TODO appLogic will handle routing after claim creation
    const route = routeWithParams("claims.name", {
      claim_id: claim.application_id,
    });

    router.push(route);
  };

  useEffect(() => {
    appLogic.loadClaims();
  }, [appLogic]);

  return (
    <React.Fragment>
      <Title>{t("pages.index.title")}</Title>

      {appLogic.claims ? (
        <section className="border-bottom border-base-lighter padding-bottom-2 margin-bottom-5">
          <Heading level="2">{t("pages.index.activeClaimsHeading")}</Heading>
          {appLogic.claims.items.map((claim, index) => (
            <DashboardClaimCard
              key={claim.application_id}
              claim={claim}
              number={index + 1}
            />
          ))}
        </section>
      ) : null}

      <Heading className="margin-top-3" level="2">
        {t("pages.index.newClaimHeading")}
      </Heading>
      <Heading level="3">{t("pages.index.claimChecklistHeader")}</Heading>

      <ul className="usa-list">
        <li>{t("pages.index.claimChecklistContactInformation")}</li>
        <li>{t("pages.index.claimChecklistEmploymentInformation")}</li>
        <li>{t("pages.index.claimChecklistReasonForLeave")}</li>
        <li>{t("pages.index.claimChecklistDateOfLeave")}</li>
        <li>{t("pages.index.claimChecklistWhereToSendBenefits")}</li>
      </ul>
      <form onSubmit={handleSubmit}>
        <Button
          type="submit"
          name="new-claim"
          variation={appLogic.claims ? "outline" : undefined}
        >
          {t("pages.index.createClaimButtonText")}
        </Button>
      </form>
    </React.Fragment>
  );
};

Index.propTypes = {
  appLogic: PropTypes.object.isRequired,
  user: PropTypes.instanceOf(User),
};

export default Index;
