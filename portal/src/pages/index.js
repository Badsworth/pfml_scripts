import React, { useEffect } from "react";
import { Auth } from "@aws-amplify/auth";
import PropTypes from "prop-types";
import Title from "../components/Title";
import routes from "../routes";
import { useTranslation } from "../locales/i18n";

export const Index = (props) => {
  const { appLogic } = props;
  const { t } = useTranslation();

  // Temporary redirect logic while this page is still pending content
  useEffect(() => {
    // eslint-disable-next-line promise/catch-or-return
    Auth.currentUserInfo().then((userInfo) => {
      if (userInfo) {
        return appLogic.portalFlow.goTo(routes.claims.dashboard);
      }

      return appLogic.portalFlow.goTo(routes.auth.login);
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <React.Fragment>
      <Title>{t("pages.index.title")}</Title>
    </React.Fragment>
  );
};

Index.propTypes = {
  appLogic: PropTypes.shape({
    portalFlow: PropTypes.shape({
      goTo: PropTypes.func.isRequired,
    }).isRequired,
  }).isRequired,
};

export default Index;
