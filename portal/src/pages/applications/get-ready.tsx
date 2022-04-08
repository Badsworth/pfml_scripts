import { IconLaptop, IconPhone } from "@massds/mayflower-react/dist/Icon";
import withBenefitsApplications, {
  WithBenefitsApplicationsProps,
} from "../../hoc/withBenefitsApplications";
import Alert from "../../components/core/Alert";
import ButtonLink from "../../components/ButtonLink";
import Details from "../../components/core/Details";
import Heading from "../../components/core/Heading";
import Icon from "../../components/core/Icon";
import Link from "next/link";
import MfaSetupSuccessAlert from "src/components/MfaSetupSuccessAlert";
import React from "react";
import Title from "../../components/core/Title";
import { Trans } from "react-i18next";
import { getMaxBenefitAmount } from "src/utils/getMaxBenefitAmount";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";

export interface GetReadyProps extends WithBenefitsApplicationsProps {
  query: {
    smsMfaConfirmed?: string;
    account_converted?: string;
  };
}

export const GetReady = (props: GetReadyProps) => {
  const { appLogic, claims, query } = props;
  const { t } = useTranslation();

  const hasClaims = !claims.isEmpty;
  const accountConverted = query?.account_converted === "true";

  const iconClassName =
    "margin-right-1 text-secondary text-middle margin-top-neg-05";

  const alertIconProps = {
    className: iconClassName,
    height: 20,
    width: 20,
    fill: "currentColor",
  };

  const maxBenefitAmount = getMaxBenefitAmount();

  return (
    <React.Fragment>
      {accountConverted && (
        <Alert
          className="margin-bottom-3"
          heading={t("pages.getReady.convertHeading")}
          state="success"
        >
          {t("pages.getReady.convertDescription")}
        </Alert>
      )}
      {hasClaims && (
        <Link href={appLogic.portalFlow.getNextPageRoute("SHOW_APPLICATIONS")}>
          <a className="display-inline-block margin-bottom-5">
            {t("pages.getReady.applicationsLink")}
          </a>
        </Link>
      )}
      {query?.smsMfaConfirmed && <MfaSetupSuccessAlert />}

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
              <a
                href={routes.external.massgov.healthcareProviderForm}
                target="_blank"
                rel="noopener"
              />
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
        <Heading level="4">
          {t("pages.getReady.stepTwoCaringLeaveSubhead")}
        </Heading>
        <Trans
          i18nKey="pages.getReady.stepTwoCaringLeaveBody"
          components={{
            "caregiver-certification-form-link": (
              <a
                href={routes.external.massgov.caregiverCertificationForm}
                target="_blank"
                rel="noopener"
              />
            ),
          }}
        />
        <Heading level="2">
          <Icon className={iconClassName} name="edit" />
          {t("pages.getReady.stepThreeHeading")}
        </Heading>
        <Trans
          i18nKey="pages.getReady.stepThree"
          values={{ maxBenefitAmount }}
          components={{
            "contact-center-phone-link": (
              <a href={`tel:${t("shared.contactCenterPhoneNumber")}`} />
            ),
            "medical-bonding-link": (
              <a
                href={routes.external.massgov.medicalBonding}
                target="_blank"
                rel="noopener"
              />
            ),
            ul: <ul className="usa-list" />,
            li: <li />,
            "tax-guide-link": (
              <a
                href={routes.external.massgov.taxGuide}
                target="_blank"
                rel="noopener"
              />
            ),
            "tax-liability-link": (
              <a
                href={routes.external.massgov.taxLiability}
                target="_blank"
                rel="noopener"
              />
            ),
            "benefits-amount-details-link": (
              <a
                href={
                  routes.external.massgov.benefitsGuide_benefitsAmountDetails
                }
                target="_blank"
                rel="noopener"
              />
            ),
          }}
        />
        <ButtonLink
          className="margin-top-3 margin-bottom-3"
          href={appLogic.portalFlow.getNextPageRoute("START_APPLICATION")}
        >
          {t("pages.getReady.createClaimButton")}
        </ButtonLink>

        <Details label={t("pages.getReady.startByPhoneLabel")}>
          <p>{t("pages.getReady.startByPhoneDescription")}</p>
          <Link
            href={appLogic.portalFlow.getNextPageRoute("IMPORT_APPLICATION")}
          >
            <a className="display-inline-block margin-bottom-5">
              {t("pages.getReady.addApplication")}
            </a>
          </Link>
        </Details>
      </div>
    </React.Fragment>
  );
};

export default withBenefitsApplications(GetReady);
