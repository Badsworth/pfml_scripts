import PropTypes from "prop-types";
import React from "react";

/**
 * Displays auth links and info about the user if they're logged in
 * @returns {React.Component}
 */
const AuthNav = props => {
  if (props.user) {
    // TODO: Add logout link
    // https://trello.com/c/eNrRdqBl
    return (
      <React.Fragment>
        Logged in as: {props.user.name}
        <nav>
          <a href="#todo">Log out</a>
        </nav>
      </React.Fragment>
    );
  }

  // TODO: Set the correct login link
  // https://trello.com/c/0Vpplf0d
  return <a href="#todo">Log in</a>;
};

AuthNav.propTypes = {
  user: PropTypes.shape({
    name: PropTypes.string
  })
};

export default AuthNav;
