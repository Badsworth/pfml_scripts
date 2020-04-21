import ButtonLink from "../components/ButtonLink";
import Heading from "../components/Heading";
import React from "react";
import Title from "../components/Title";
import routes from "../routes";
import { useTranslation } from "../locales/i18n";

/**
 * The page a user is redirected to by default after
 * successfully authenticating.
 * @returns {React.Component}
 */
const Index = () => {
  const { t } = useTranslation();

  // TODO As part of implementing "In progress claims" (see https://lwd.atlassian.net/browse/CP-251)
  // we'll need to create a new claim when the user clicks "Create a New Claim"
  // (eventually this will be an API call to POSTS /v1/claims or /v1/applications once that endpoint is ready)
  // and add the claim to the claims state with `props.claims.add(claim)`

  return (
    <React.Fragment>
      <Title>{t("pages.index.pageHeader")}</Title>

      <Heading level="3">{t("pages.index.claimChecklistHeader")}</Heading>

      <ul className="usa-list">
        <li>{t("pages.index.claimChecklistContact")}</li>
        <li>{t("pages.index.claimChecklistEmployment")}</li>
        <li>{t("pages.index.claimChecklistReasonForLeave")}</li>
        <li>{t("pages.index.claimChecklistDateOfLeave")}</li>
        <li>{t("pages.index.claimChecklistWhereToSendBenefits")}</li>
      </ul>

      <ButtonLink href={routes.claims.name}>
        {t("pages.index.createClaimButtonText")}
      </ButtonLink>
    </React.Fragment>
  );
};

export default Index;
