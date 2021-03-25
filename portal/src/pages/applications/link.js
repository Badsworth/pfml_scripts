import FormLabel from "../../components/FormLabel"
import InputText from "../../components/InputText";
import Button from "../../components/Button";
import PropTypes from "prop-types";
import React from "react"
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps"
import useThrottledHandler from "../../hooks/useThrottledHandler"

export const LinkApplication = (props) => {
  const { formState, updateFields } = useFormState({caseNumber: ""});
  const { appLogic } = props;
  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });

  const handleSubmit = useThrottledHandler(async (event) => {
    event.preventDefault();
    // needs auth
    await appLogic.claims.link(formState.caseNumber)
  });

  return (
    <React.Fragment>
    <form className="usa-form" onSubmit={handleSubmit} method="post">
      <FormLabel>Enter your NTN number to link your application</FormLabel>
      <InputText
        {...getFunctionalInputProps("caseNumber")}
        type="text"
        // label={t("pages.link.caseNumber")}
        smallLabel
      />
      <Button type="submit" loading={handleSubmit.isThrottled}>
        Submit
        {/* {t("pages.authCreateAccount.createAccountButton")} */}
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
