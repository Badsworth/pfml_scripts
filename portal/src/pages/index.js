import Button from "../components/Button";
import Collection from "../models/Collection";
import DashboardClaimCard from "../components/DashboardClaimCard";
import Heading from "../components/Heading";
import PropTypes from "prop-types";
import React from "react";
import Title from "../components/Title";
import claimsApi from "../api/claimsApi";
import routeWithParams from "../utils/routeWithParams";
import useHandleSave from "../hooks/useHandleSave";

import { useRouter } from "next/router";
import { useTranslation } from "../locales/i18n";

/**
 * "Dashboard" - Where a user is redirected to after successfully authenticating.
 */

const Index = ({ claims, addClaim }) => {
  const { t } = useTranslation();
  const router = useRouter();

  const createClaim = useHandleSave(claimsApi.createClaim, (result) => {
    addClaim(result.claim);

    const route = routeWithParams("claims.name", {
      claim_id: result.claim.claim_id,
    });
    router.push(route);
  });

  const handleClaimButtonClick = () => createClaim();

  return (
    <React.Fragment>
      <Title>{t("pages.index.title")}</Title>

      {claims.ids.length ? (
        <section className="border-bottom border-base-lighter padding-bottom-2 margin-bottom-5">
          <Heading level="2">{t("pages.index.activeClaimsHeading")}</Heading>
          {claims.ids.map((claim_id, index) => (
            <DashboardClaimCard
              key={claim_id}
              claim={claims.get(claim_id)}
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
        <li>{t("pages.index.claimChecklistContact")}</li>
        <li>{t("pages.index.claimChecklistEmployment")}</li>
        <li>{t("pages.index.claimChecklistReasonForLeave")}</li>
        <li>{t("pages.index.claimChecklistDateOfLeave")}</li>
        <li>{t("pages.index.claimChecklistWhereToSendBenefits")}</li>
      </ul>

      <Button
        onClick={handleClaimButtonClick}
        variation={claims.ids.length ? "outline" : undefined}
      >
        {t("pages.index.createClaimButtonText")}
      </Button>
    </React.Fragment>
  );
};

Index.propTypes = {
  addClaim: PropTypes.func,
  claims: PropTypes.instanceOf(Collection).isRequired,
};

export default Index;
