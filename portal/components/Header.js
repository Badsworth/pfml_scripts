import AuthNav from "./AuthNav";
import PropTypes from "prop-types";
import React from "react";

/**
 * Global page header, displayed at the top of every page.
 * @param {object} props
 * @returns {React.Component}
 */
const Header = props => (
  <header>
    <a href="#main">Skip to main content</a>
    <h1>Paid Family and Medical Leave</h1>
    <AuthNav user={props.user} />
    <p>Built for Environment: {process.env.envName}</p>
  </header>
);

Header.propTypes = {
  user: PropTypes.object
};

export default Header;
