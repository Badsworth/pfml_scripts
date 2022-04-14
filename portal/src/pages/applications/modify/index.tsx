import { IconLaptop, IconPhone } from "@massds/mayflower-react/dist/Icon";
import BackButton from "../../../components/BackButton";
import Button from "../../../components/core/Button";
import Heading from "../../../components/core/Heading";
import PageNotFound from "../../../components/PageNotFound";
import React from "react";
import Title from "../../../components/core/Title";
import { Trans } from "react-i18next";
import { isFeatureEnabled } from "../../../services/featureFlags";
import routes from "../../../routes";
import { useTranslation } from "../../../locales/i18n";

interface IndexProps {
  query: {
    absence_id: string;
  };
}

export const Index = (_props: IndexProps) => {
  const { t } = useTranslation();

  /* eslint-disable require-await */
  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    // Do nothing for now
  };

  // TODO(PORTAL-2064): Remove claimantShowModifications feature flag
  if (!isFeatureEnabled("claimantShowModifications")) return <PageNotFound />;

  const iconProps = {
    className: "margin-right-1 text-secondary text-middle",
    height: 20,
    width: 20,
    fill: "currentColor",
  };

  return (
    <React.Fragment>
      <BackButton
        label={t("pages.claimsModifyIndex.backButtonLabel")}
        href={routes.applications.index}
      />
      <form onSubmit={handleSubmit} className="usa-form">
        <Title small>{t("pages.claimsModifyIndex.title")}</Title>
        <Heading level="2">{t("pages.claimsModifyIndex.heading")}</Heading>
        <Heading level="3" className="margin-top-3">
          <IconLaptop {...iconProps} />
          {t("pages.claimsModifyIndex.onlineHeading")}
        </Heading>

        <Trans
          i18nKey="pages.claimsModifyIndex.onlineBody"
          components={{
            ul: <ul className="usa-list" />,
            li: <li />,
          }}
        />

        <Heading level="3">
          <IconPhone {...iconProps} />
          {t("pages.claimsModifyIndex.phoneHeading")}
        </Heading>

        <Trans
          i18nKey="pages.claimsModifyIndex.phoneBody"
          components={{
            "contact-center-phone-link": (
              <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
            ),
            ul: <ul className="usa-list" />,
            li: <li />,
          }}
        />

        <Trans i18nKey="pages.claimsModifyIndex.instructions" />

        <Button className="margin-top-4" type="submit">
          {t("pages.claimsModifyIndex.button")}
        </Button>
      </form>
    </React.Fragment>
  );
};

export default Index;
