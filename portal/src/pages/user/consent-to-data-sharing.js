import Accordion from "../../components/Accordion";
import AccordionItem from "../../components/AccordionItem";
import Alert from "../../components/Alert";
import Button from "../../components/Button";
import PropTypes from "prop-types";
import React from "react";
import Title from "../../components/Title";
import User from "../../models/User";
import routes from "../../routes";
import useHandleSave from "../../hooks/useHandleSave";
import { useRouter } from "next/router";
import { useTranslation } from "../../locales/i18n";
import usersApi from "../../api/usersApi";

const ConsentToDataSharing = (props) => {
  const { t } = useTranslation();
  const router = useRouter();

  const handleSave = useHandleSave(
    () =>
      usersApi.updateUser(props.user.user_id, {
        consented_to_data_sharing: true,
      }),
    (result) => props.setUser(result.user)
  );

  const handleSubmit = async (event) => {
    event.preventDefault();
    await handleSave();
    router.push(routes.home);
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
          <p
            dangerouslySetInnerHTML={{
              __html: t("pages.userConsentToDataSharing.fullUserAgreementBody"),
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
  user: PropTypes.instanceOf(User).isRequired,
  setUser: PropTypes.func.isRequired,
};

export default ConsentToDataSharing;
