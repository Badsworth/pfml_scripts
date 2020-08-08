import Accordion from "../../components/Accordion";
import AccordionItem from "../../components/AccordionItem";
import Alert from "../../components/Alert";
import Button from "../../components/Button";
import PropTypes from "prop-types";
import React from "react";
import Title from "../../components/Title";
import routes from "../../routes";
import { useTranslation } from "../../locales/i18n";

const ConsentToDataSharing = (props) => {
  const { t } = useTranslation();
  const {
    users: { user, updateUser },
  } = props.appLogic;

  const handleSave = () =>
    updateUser(user.user_id, {
      consented_to_data_sharing: true,
    });

  const handleSubmit = async (event) => {
    event.preventDefault();
    await handleSave();
  };

  return (
    <form onSubmit={handleSubmit} className="usa-form measure-5">
      <Title>{t("pages.userConsentToDataSharing.title")}</Title>
      <p className="margin-bottom-2">
        {t("pages.userConsentToDataSharing.intro")}
      </p>

      <Accordion>
        <AccordionItem
          heading={t("pages.userConsentToDataSharing.applicationUsageHeading")}
        >
          <p>{t("pages.userConsentToDataSharing.applicationUsageIntro")}</p>
          <ul className="usa-list">
            {t("pages.userConsentToDataSharing.applicationUsageList", {
              returnObjects: true,
            }).map((listItemContent, index) => (
              <li key={index}>{listItemContent}</li>
            ))}
          </ul>
        </AccordionItem>
        <AccordionItem
          heading={t("pages.userConsentToDataSharing.dataUsageHeading")}
        >
          <p>{t("pages.userConsentToDataSharing.dataUsageBody")}</p>
        </AccordionItem>
        <AccordionItem
          heading={t("pages.userConsentToDataSharing.fullUserAgreementHeading")}
        >
          {/* TODO CP-713: consider using i18n Trans component */}
          <p
            dangerouslySetInnerHTML={{
              __html: t(
                "pages.userConsentToDataSharing.fullUserAgreementBody",
                {
                  massPrivacyPolicyUrl: routes.external.massgov.privacyPolicy,
                  massInformedConsentUrl:
                    routes.external.massgov.informedConsent,
                }
              ),
            }}
          />
        </AccordionItem>
      </Accordion>

      <Alert noIcon state="info">
        {t("pages.userConsentToDataSharing.agreementBody")}
      </Alert>

      <Button type="submit">
        {t("pages.userConsentToDataSharing.continueButton")}
      </Button>
    </form>
  );
};

ConsentToDataSharing.propTypes = {
  appLogic: PropTypes.object.isRequired,
};

export default ConsentToDataSharing;
