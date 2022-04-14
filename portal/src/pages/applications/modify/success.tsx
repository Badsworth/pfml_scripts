import withBenefitsApplication, {
  WithBenefitsApplicationProps,
} from "../../../hoc/withBenefitsApplication";
import BackButton from "../../../components/BackButton";
import Heading from "../../../components/core/Heading";
import { IconCalendar } from "@massds/mayflower-react/dist/Icon";
import PageNotFound from "../../../components/PageNotFound";
import React from "react";
import Title from "../../../components/core/Title";
import { Trans } from "react-i18next";
import { isFeatureEnabled } from "../../../services/featureFlags";
import routeWithParams from "../../../utils/routeWithParams";
import routes from "../../../routes";
import { useTranslation } from "../../../locales/i18n";

export const Success = (props: WithBenefitsApplicationProps) => {
  const { claim } = props;
  const { t } = useTranslation();

  // TODO(PORTAL-2064): Remove claimantShowModifications feature flag
  if (!isFeatureEnabled("claimantShowModifications")) return <PageNotFound />;

  const iconProps = {
    className: "margin-right-2 text-secondary text-middle",
    height: 30,
    width: 30,
    fill: "currentColor",
  };

  return (
    <React.Fragment>
      <BackButton
        label={t("pages.claimsModifySuccess.backButtonLabel")}
        href={routes.applications.index}
      />
      <Title>{t("pages.claimsModifySuccess.title")}</Title>
      <Heading level="2">
        <IconCalendar {...iconProps} />
        {t("pages.claimsModifySuccess.adjudicationProcessHeading")}
      </Heading>

      <Trans
        i18nKey="pages.claimsModifySuccess.adjudicationProcess"
        components={{
          "contact-center-phone-link": (
            <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
          ),
          "track-status-link": (
            <a
              href={routeWithParams("applications.status.claim", {
                absence_id: claim.fineos_absence_id,
              })}
            />
          ),
          ul: <ul className="usa-list" />,
          li: <li />,
        }}
      />
    </React.Fragment>
  );
};

export default withBenefitsApplication(Success);
