import Alert from "src/components/Alert";
import React from "react";

export default {
  title: "Components/Alert",
  component: Alert,
  argTypes: {
    state: {
      control: "radio",
    },
    heading: {
      defaultValue: "Please fix the following errors",
      control: {
        type: "text",
      },
    },
    children: {
      defaultValue: "Mailing address is required",
      control: {
        type: "text",
      },
    },
  },
};

export const ErrorAlert = (args) => <Alert {...args} />;

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
    Here is an info alert without an icon.
  </Alert>
);

export const Slim = () => (
  <Alert state="info" slim>
    This info alert is slim.
  </Alert>
);

export const neutral = () => (
  <Alert state="info" neutral>
    This info alert has a neutral background color.
  </Alert>
);

export const AutoWidth = () => (
  <React.Fragment>
    <Alert state="info" autoWidth>
      This alert's width fits its content.
    </Alert>
    <Alert state="info" autoWidth>
      This alert is also only as wide as its content. However, its content is
      long enough to wrap to multiple lines and cause the alert to fill the
      width of its container.
    </Alert>
  </React.Fragment>
);
