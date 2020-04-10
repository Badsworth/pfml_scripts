import ButtonLink from "../components/ButtonLink";
import Heading from "../components/Heading";
import React from "react";
import Title from "../components/Title";
import routes from "../routes";
import { useTranslation } from "react-i18next";

/**
 * The page a user is redirected to by default after
 * successfully authenticating.
 * @returns {React.Component}
 */
const Index = () => {
  const { t } = useTranslation();

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
