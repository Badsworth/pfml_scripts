import Alert from "src/components/Alert";
import React from "react";

export default {
  title: "Components/Alert",
  component: Alert,
};

export const ErrorAlert = () => (
  <Alert heading="Please fix the following errors">
    Mailing address is required
  </Alert>
);

export const ErrorAlertTextOnly = () => (
  <Alert>
    The following errors were encountered:
    <ul className="usa-list">
      <li>First name is required</li>
      <li>Social security number is required</li>
    </ul>
  </Alert>
);

export const Info = () => (
  <Alert state="info">Applications for medical leave are now open</Alert>
);

export const Success = () => (
  <Alert state="success">
    Your application has been submitted successfully
  </Alert>
);

export const Warning = () => (
  <Alert state="warning">You need to submit additional documents</Alert>
);

export const NoIcon = () => (
  <Alert state="info" noIcon>
    Here is some called-out information.
  </Alert>
);
