import Accordion from "../../components/core/Accordion";
import AccordionItem from "../../components/core/AccordionItem";
import Alert from "../../components/core/Alert";
import { AppLogic } from "../../hooks/useAppLogic";
import Button from "../../components/core/Button";
import React from "react";
import Title from "../../components/core/Title";
import { Trans } from "react-i18next";
import User from "../../models/User";
import routes from "../../routes";
import tracker from "../../services/tracker";
import useThrottledHandler from "../../hooks/useThrottledHandler";
import { useTranslation } from "../../locales/i18n";
import withUser from "../../hoc/withUser";

interface ConsentToDataSharingProps {
  appLogic: AppLogic;
  user: User;
}

export const ConsentToDataSharing = (props: ConsentToDataSharingProps) => {
  const { t } = useTranslation();
  const { appLogic, user } = props;
  const { updateUser } = appLogic.users;

  const handleSave = () =>
    updateUser(user.user_id, {
      consented_to_data_sharing: true,
    });

  const handleSubmit = useThrottledHandler(async (event) => {
    event.preventDefault();
    await handleSave();
    tracker.trackEvent("User consented to data sharing", {});
  });

  const roleContext = user.hasEmployerRole ? "employer" : "user";

  return (
    <form onSubmit={handleSubmit} className="usa-form" method="post">
      <Title>{t("pages.userConsentToDataSharing.title")}</Title>
      <p className="margin-bottom-2">
        {t("pages.userConsentToDataSharing.intro")}
      </p>

      <Accordion>
        <AccordionItem
          heading={t("pages.userConsentToDataSharing.applicationUsageHeading", {
            context: roleContext,
          })}
        >
          <p>{t("pages.userConsentToDataSharing.applicationUsageIntro")}</p>
          <ul className="usa-list">
            {t<string, string[]>(
              "pages.userConsentToDataSharing.applicationUsageList",
              {
                returnObjects: true,
                context: roleContext,
              }
            ).map((listItemContent, index) => (
              <li key={index}>{listItemContent}</li>
            ))}
          </ul>
        </AccordionItem>

        <AccordionItem
          heading={t("pages.userConsentToDataSharing.dataUsageHeading")}
        >
          <p>
            {t("pages.userConsentToDataSharing.dataUsageBody", {
              context: roleContext,
            })}
          </p>
        </AccordionItem>

        <AccordionItem
          heading={t("pages.userConsentToDataSharing.fullUserAgreementHeading")}
        >
          <p>
            <Trans
              i18nKey="pages.userConsentToDataSharing.fullUserAgreementBody"
              components={{
                // Anchor tag content will be added by Trans component from locale file
                // eslint-disable-next-line jsx-a11y/anchor-has-content
                "informed-consent-link": (
                  <a
                    href={routes.external.massgov.informedConsent}
                    rel="noopener noreferrer"
                    target="_blank"
                  />
                ),
                // Anchor tag content will be added by Trans component from locale file
                // eslint-disable-next-line jsx-a11y/anchor-has-content
                "privacy-policy-link": (
                  <a
                    href={routes.external.massgov.privacyPolicy}
                    rel="noopener noreferrer"
                    target="_blank"
                  />
                ),
              }}
            />
          </p>
        </AccordionItem>
      </Accordion>

      <Alert state="info" noIcon>
        <p>{t("pages.userConsentToDataSharing.agreementBody")}</p>
        <Button type="submit" loading={handleSubmit.isThrottled}>
          {t("pages.userConsentToDataSharing.continueButton")}
        </Button>
      </Alert>
    </form>
  );
};

export default withUser(ConsentToDataSharing);
