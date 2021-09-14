/* eslint react/prop-types: 0 */
import React from "react";
import User from "../../src/models/User";
import { render } from "@testing-library/react";
import useAppLogic from "../../src/hooks/useAppLogic";

const authenticateUser = (appLogic) => {
  appLogic.auth.requireLogin = jest.fn();
  appLogic.users.requireUserConsentToDataAgreement = jest.fn();
  appLogic.users.requireUserRole = jest.fn();
  appLogic.users.user = new User({
    consented_to_data_sharing: true,
    email_address: "unique@miau.com",
  });
};

const PageWithAppLogic = ({
  PageComponent,
  addCustomSetup,
  isLoggedIn = true,
  ...props
}) => {
  const appLogic = useAppLogic();

  if (isLoggedIn) {
    authenticateUser(appLogic);
  }

  if (addCustomSetup) {
    addCustomSetup(appLogic);
  }

  return <PageComponent appLogic={appLogic} {...props} />;
};

/**
 * @param {Function} PageComponent - A function that returns React Component to be rendered
 * @param {object} options - An object of custom options to pass through to the component
 * @param {Function} options.addCustomSetup - Function that receives appLogic as a param, used to customize appLogic setup
 * @param {boolean} options.isLoggedIn - Boolean flag to specify whether or not to authenticate user
 * @param {object} props - For any additional arbitrary props
 *
 * @returns {object} RTL render function result: https://testing-library.com/docs/react-testing-library/api#render-result
 */
export const renderPage = (PageComponent, options = {}, props = {}) => {
  const component = (
    <PageWithAppLogic
      PageComponent={PageComponent}
      addCustomSetup={options.addCustomSetup}
      isLoggedIn={options.isLoggedIn}
      {...props}
    />
  );

  return render(component, { ...options });
};
