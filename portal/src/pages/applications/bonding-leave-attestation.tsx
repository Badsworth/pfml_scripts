import Alert from "../../components/Alert";
import BackButton from "../../components/BackButton";
import ButtonLink from "../../components/ButtonLink";
import React from "react";
import Title from "../../components/Title";
import { Trans } from "react-i18next";
import usePortalFlow from "../../hooks/usePortalFlow";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplication from "../../hoc/withBenefitsApplication";

interface BondingLeaveAttestationProps {
  appLogic: {
    portalFlow?: ReturnType<typeof usePortalFlow>;
  };
  query: any;
}

export const BondingLeaveAttestation = (
  props: BondingLeaveAttestationProps
) => {
  const { t } = useTranslation();
  const { appLogic, query } = props;

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
          href={appLogic.portalFlow.getNextPageRoute("CONTINUE", {}, query)}
        >
          {t("pages.claimsBondingLeaveAttestation.submitApplicationButton")}
        </ButtonLink>
      </Alert>
    </React.Fragment>
  );
};

export default withBenefitsApplication(BondingLeaveAttestation);
