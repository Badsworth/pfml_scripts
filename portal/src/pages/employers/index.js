/* eslint-disable react/no-unused-prop-types */
import PropTypes from "prop-types";
import routes from "../../../src/routes";
import { useEffect } from "react";
import { useRouter } from "next/router";
import withUser from "../../hoc/withUser";

export const Index = () => {
  const router = useRouter();
  const redirectUrl = `${routes.employers.review}`;

  useEffect(() => {
    router.push(redirectUrl);
  });

  return null;
};

Index.propTypes = {
  appLogic: PropTypes.object.isRequired,
};

export default withUser(Index);
