import { Auth } from "aws-amplify";
import PropTypes from "prop-types";
import React from "react";

/**
 * Displays auth links and info about the user if they're logged in
 * @returns {React.Component}
 */
const AuthNav = props => {
  const handleSignOut = () => {
    Auth.signOut();
  };

  if (props.user) {
    return (
      <React.Fragment>
        Logged in as: {props.user.username}
        <nav>
          <button onClick={handleSignOut}>Log out</button>
        </nav>
      </React.Fragment>
    );
  }
};

AuthNav.propTypes = {
  user: PropTypes.shape({
    username: PropTypes.string
  })
};

export default AuthNav;
