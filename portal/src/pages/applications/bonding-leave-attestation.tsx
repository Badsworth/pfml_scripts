import withBenefitsApplication, {
  WithBenefitsApplicationProps,
} from "../../hoc/withBenefitsApplication";
import Alert from "../../components/Alert";
import BackButton from "../../components/BackButton";
import ButtonLink from "../../components/ButtonLink";
import React from "react";
import Title from "../../components/Title";
import { Trans } from "react-i18next";
import { useTranslation } from "../../locales/i18n";

export const BondingLeaveAttestation = (
  props: WithBenefitsApplicationProps
) => {
  const { t } = useTranslation();
  const { appLogic, claim } = props;

  return (
    <React.Fragment>
      <BackButton />
      <Title>{t("pages.claimsBondingLeaveAttestation.title")}</Title>
      <Trans
        i18nKey="pages.claimsBondingLeaveAttestation.lead"
        components={{ ul: <ul className="usa-list" />, li: <li /> }}
      />
      <Alert className="measure-6" state="info" noIcon>
        <p>{t("pages.claimsBondingLeaveAttestation.truthAttestation")}</p>
        <ButtonLink
          className="text-no-underline text-white"
          href={appLogic.portalFlow.getNextPageRoute(
            "CONTINUE",
            {},
            { claim_id: claim.application_id }
          )}
        >
          {t("pages.claimsBondingLeaveAttestation.submitApplicationButton")}
        </ButtonLink>
      </Alert>
    </React.Fragment>
  );
};

export default withBenefitsApplication(BondingLeaveAttestation);
