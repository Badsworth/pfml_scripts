import { IconLaptop, IconPhone } from "@massds/mayflower-react/dist/Icon";
import Alert from "../../components/Alert";
import ButtonLink from "../../components/ButtonLink";
import ClaimCollection from "../../models/ClaimCollection";
import Heading from "../../components/Heading";
import Icon from "../../components/Icon";
import Link from "next/link";
import PropTypes from "prop-types";
import React from "react";
import Title from "../../components/Title";
import { Trans } from "react-i18next";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";
import withClaims from "../../hoc/withClaims";

export const ConvertToEmployer = (props) => {
  const { appLogic, claims, user } = props;
  const { t } = useTranslation();
  const { updateUser } = appLogic.users;
  const hasClaims = !claims.isEmpty;
  const iconClassName =
    "margin-right-1 text-secondary text-middle margin-top-neg-05";
  const alertIconProps = {
    className: iconClassName,
    height: 20,
    width: 20,
    fill: "currentColor",
  };

  const handleSave = () =>
    updateUser(user.user_id, {
      consented_to_data_sharing: true,
    });

  return (
    <React.Fragment>

      <Title>{t("pages.convertToEmployer.title")}</Title>

      {hasClaims && (
        <Alert
          heading={t("pages.getReady.alertHeading")}
          state="info"
          neutral
          className="margin-bottom-3"
        >
          <Heading level="3" className="margin-top-3">
            <IconLaptop {...alertIconProps} />
            {t("pages.getReady.alertOnlineHeading")}
          </Heading>

          <Trans
            i18nKey="pages.getReady.alertOnline"
            components={{
              ul: <ul className="usa-list" />,
              li: <li />,
            }}
          />

          <Heading level="3">
            <IconPhone {...alertIconProps} />
            {t("pages.getReady.alertPhoneHeading")}
          </Heading>

          <Trans
            i18nKey="pages.getReady.alertPhone"
            components={{
              "contact-center-phone-link": (
                <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
              ),
              "benefits-timeline-link": (
                <a
                  href={routes.external.massgov.benefitsTimeline_2020December2}
                />
              ),
              ul: <ul className="usa-list" />,
              li: <li />,
            }}
          />
        </Alert>
      )}

      <div className="measure-6">

        <ButtonLink
          className="margin-top-3 margin-bottom-8"
          href={appLogic.portalFlow.getNextPageRoute("START_APPLICATION")}
        >
          {t("pages.getReady.createClaimButton")}
        </ButtonLink>
      </div>
    </React.Fragment>
  );
};

ConvertToEmployer.propTypes = {
  appLogic: PropTypes.shape({
    portalFlow: PropTypes.shape({
      getNextPageRoute: PropTypes.func.isRequired,
      pathname: PropTypes.string.isRequired,
    }),
  }).isRequired,
  claims: PropTypes.instanceOf(ClaimCollection).isRequired,
};

export default withClaims(ConvertToEmployer);
