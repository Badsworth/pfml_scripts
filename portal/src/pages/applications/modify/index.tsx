import { IconLaptop, IconPhone } from "@massds/mayflower-react/dist/Icon";
import { AppLogic } from "../../../hooks/useAppLogic";
import BackButton from "../../../components/BackButton";
import Button from "../../../components/core/Button";
import ChangeRequest from "src/models/ChangeRequest";
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
  appLogic: AppLogic;
}

export const Index = (props: IndexProps) => {
  const { t } = useTranslation();

  /* eslint-disable require-await */
  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    // TODO (PORTAL-2144): POST change request and return it
    const changeRequest = new ChangeRequest({
      change_request_id: "change-request-id",
    });

    props.appLogic.portalFlow.goToNextPage(
      { changeRequest },
      {
        absence_id: props.query.absence_id,
        change_request_id: changeRequest.change_request_id,
      }
    );
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
