/* eslint-disable react/no-unused-prop-types */
import Link from "next/link";
import PropTypes from "prop-types";
import React from "react";
import routes from "../../routes";
import withUser from "../../hoc/withUser";

export const Index = () => {
  return (
    <div>
      <Link href={routes.employers.review}>Review claim</Link>
    </div>
  );
};

Index.propTypes = {
  appLogic: PropTypes.object.isRequired,
};

export default withUser(Index);
