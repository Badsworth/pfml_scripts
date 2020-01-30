import AuthNav from "./AuthNav";
import PropTypes from "prop-types";
import React from "react";
import { useTranslation } from "react-i18next";

/**
 * Global page header, displayed at the top of every page.
 * @param {object} props
 * @returns {React.Component}
 */
const Header = props => {
  const { t } = useTranslation();

  return (
    <header>
      <a href="#main">{t("components.header.skipToContent")}</a>
      <h1>{t("components.header.appTitle")}</h1>
      <AuthNav user={props.user} />
      <p>Built for Environment: {process.env.envName}</p>
    </header>
  );
};

Header.propTypes = {
  user: PropTypes.object
};

export default Header;
