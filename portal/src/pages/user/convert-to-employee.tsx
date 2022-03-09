import withUser, { WithUserProps } from "../../hoc/withUser";
import Alert from "../../components/core/Alert";
import Button from "../../components/core/Button";
import React from "react";
import Title from "../../components/core/Title";
import routes from "../../routes";
import useThrottledHandler from "../../hooks/useThrottledHandler";
import { useTranslation } from "../../locales/i18n";

export const ConvertToEmployee = (props: WithUserProps) => {
  const { appLogic, user } = props;
  const { t } = useTranslation();
  const { convertUserToEmployee } = appLogic.users;

  const handleSubmit = useThrottledHandler(async (event) => {
    event.preventDefault();
    await convertUserToEmployee(user.user_id);
  });

  // If user is already an Employee, go to the applications page.
  if (!user.hasEmployerRole) {
    appLogic.portalFlow.goTo(
      routes.applications.getReady,
      {},
      { redirect: true }
    );
    return null;
  }

  // If user is verified leave admin, do not allow account conversion
  if (!user.hasOnlyUnverifiedEmployers) {
    appLogic.portalFlow.goToPageFor(
      "PREVENT_CONVERSION",
      {},
      {},
      { redirect: true }
    );
    return null;
  }

  return (
    <React.Fragment>
      <Title>{t("pages.convertToEmployee.title")}</Title>
      <Alert
        heading={t("pages.convertToEmployee.alertHeading")}
        state="warning"
        className="margin-bottom-3"
      >
        <p>{t("pages.convertToEmployee.alertDescription")}</p>
      </Alert>
      <form className="usa-form" onSubmit={handleSubmit} method="post">
        <Button type="submit" loading={handleSubmit.isThrottled}>
          {t("pages.convertToEmployee.submit")}
        </Button>
      </form>
    </React.Fragment>
  );
};

export default withUser(ConvertToEmployee);
