import { IconLaptop, IconPhone } from "@massds/mayflower-react/dist/Icon";
import Alert from "../../components/Alert";
import BenefitsApplicationCollection from "../../models/BenefitsApplicationCollection";
import ButtonLink from "../../components/ButtonLink";
import Heading from "../../components/Heading";
import Icon from "../../components/Icon";
import Link from "next/link";
import PropTypes from "prop-types";
import React from "react";
import Title from "../../components/Title";
import { Trans } from "react-i18next";
import { isFeatureEnabled } from "../../services/featureFlags";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";
import withBenefitsApplications from "../../hoc/withBenefitsApplications";

export const GetReady = (props) => {
  const { appLogic, claims } = props;
  const { t } = useTranslation();

  const hasClaims = !claims.isEmpty;

  const iconClassName =
    "margin-right-1 text-secondary text-middle margin-top-neg-05";

  const alertIconProps = {
    className: iconClassName,
    height: 20,
    width: 20,
    fill: "currentColor",
  };

  return (
    <React.Fragment>
      {hasClaims && (
        <Link href={appLogic.portalFlow.getNextPageRoute("SHOW_APPLICATIONS")}>
          <a className="display-inline-block margin-bottom-5">
            {t("pages.getReady.applicationsLink")}
          </a>
        </Link>
      )}

      <Title>{t("pages.getReady.title")}</Title>

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
          tOptions={{
            context: isFeatureEnabled("showCaringLeaveType")
              ? "caring"
              : undefined,
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

      <div className="measure-6">
        <Heading level="2">
          <Icon className={iconClassName} name="comment" />
          {t("pages.getReady.stepOneHeading")}
        </Heading>
        <Trans i18nKey="pages.getReady.stepOne" />

        <Heading level="2">
          <Icon className={iconClassName} name="upload_file" />
          {t("pages.getReady.stepTwoHeading")}
        </Heading>

        <Trans
          i18nKey="pages.getReady.stepTwoWhichPaidLeaveBody"
          components={{
            "which-paid-leave-link": (
              <a
                target="_blank"
                rel="noopener"
                href={routes.external.massgov.whichPaidLeave}
              />
            ),
          }}
        />

        <Heading level="3">
          {t("pages.getReady.stepTwoMedicalLeaveSubhead")}
        </Heading>
        <Trans
          i18nKey="pages.getReady.stepTwoMedicalLeaveBody"
          components={{
            "healthcare-provider-form-link": (
              <a href={routes.external.massgov.healthcareProviderForm} />
            ),
          }}
        />

        <Heading level="3">
          {t("pages.getReady.stepTwoFamilyLeaveSubhead")}
        </Heading>
        <Heading level="4">
          {t("pages.getReady.stepTwoBondingLeaveSubhead")}
        </Heading>

        <Trans i18nKey="pages.getReady.stepTwoBondingLeaveBody" />

        {isFeatureEnabled("showCaringLeaveType") ? (
          <React.Fragment>
            <Heading level="4">
              {t("pages.getReady.stepTwoCaringLeaveSubhead")}
            </Heading>
            <Trans
              i18nKey="pages.getReady.stepTwoCaringLeaveBody"
              components={{
                "caregiver-certification-form-link": (
                  <a
                    href={routes.external.massgov.caregiverCertificationForm}
                  />
                ),
              }}
            />
          </React.Fragment>
        ) : undefined}

        <Heading level="2">
          <Icon className={iconClassName} name="edit" />
          {t("pages.getReady.stepThreeHeading")}
        </Heading>
        <Trans
          i18nKey="pages.getReady.stepThree"
          components={{
            "contact-center-phone-link": (
              <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
            ),
            "medical-bonding-link": (
              <a href={routes.external.massgov.medicalBonding} />
            ),
            ul: <ul className="usa-list" />,
            li: <li />,
            "tax-liability-link": (
              <a href={routes.external.massgov.taxLiability} />
            ),
          }}
        />
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

GetReady.propTypes = {
  appLogic: PropTypes.shape({
    portalFlow: PropTypes.shape({
      getNextPageRoute: PropTypes.func.isRequired,
      pathname: PropTypes.string.isRequired,
    }),
  }).isRequired,
  claims: PropTypes.instanceOf(BenefitsApplicationCollection).isRequired,
};

export default withBenefitsApplications(GetReady);
