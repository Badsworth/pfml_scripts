import FormLabel from "../../components/FormLabel"
import InputCaseNumber from "../../components/InputCaseNumber";
import PropTypes from "prop-types";
import React from "react"
import useFormState from "../../hooks/useFormState";
import useFunctionalInputProps from "../../hooks/useFunctionalInputProps"

export const LinkApplication = (props) => {
  const { formState, updateFields } = useFormState({caseNumber: ""});
  const { appLogic } = props;
  const getFunctionalInputProps = useFunctionalInputProps({
    appErrors: appLogic.appErrors,
    formState,
    updateFields,
  });
  return (
    <React.Fragment>
    <form>
      <FormLabel>Enter your NTN number to link your application</FormLabel>
      <InputCaseNumber
        {...getFunctionalInputProps("case-number")}
      />
    </form>
    <p>{formState.caseNumber}</p>
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
