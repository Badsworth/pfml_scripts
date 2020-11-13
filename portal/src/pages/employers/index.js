/* eslint-disable react/no-unused-prop-types */
import PropTypes from "prop-types";
import React from "react";
import withUser from "../../hoc/withUser";

export const Index = () => {
  return <p>Welcome Page here</p>;
};

Index.propTypes = {
  appLogic: PropTypes.object.isRequired,
};

export default withUser(Index);
