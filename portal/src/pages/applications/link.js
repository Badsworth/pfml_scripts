import React from "react"
import PropTypes from "prop-types";
import { useTranslation } from "../../locales/i18n";
import InputText from "../../components/InputText";
import Button from "../../components/Button";

import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps"
import useThrottledHandler from "../../hooks/useThrottledHandler"

export const LinkApplication = (props) => {
  const { t } = useTranslation();
  const { formState, updateFields } = useFormState({ caseNumber: "" });
  const { appLogic } = props;
  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  const handleSubmit = useThrottledHandler(async (event) => {
    event.preventDefault();
    // needs auth
    const data = await appLogic.claims.link(formState.caseNumber)
    console.log("done", { data })
  });

  return (
    <React.Fragment>
      <form className="usa-form" onSubmit={handleSubmit} method="post">
        <InputText
          {...getFunctionalInputProps("caseNumber")}
          type="text"
          label={t("pages.link.caseNumber")}
          smallLabel
        />
        <Button type="submit" loading={handleSubmit.isThrottled}>
          {t("pages.link.submit")}
        </Button>
      </form>
    </React.Fragment>
  );
};

LinkApplication.propTypes = {
  appLogic: PropTypes.shape({
    portalFlow: PropTypes.shape({
      goTo: PropTypes.func.isRequired,
      pathname: PropTypes.string.isRequired,
    }).isRequired,
    appErrors: PropTypes.object.isRequired
  }).isRequired,
};

export default LinkApplication;
