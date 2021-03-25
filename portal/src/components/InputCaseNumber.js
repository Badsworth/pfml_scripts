import React, { useState } from "react";
import InputText from "./InputText";
import PropTypes from "prop-types";

const InputCaseNumber = (props) => {

  const [claimNumber, setClaimNumber] = useState("");

  const handleChange = (event) => {
    const claimNumber = event.target.value;
    setClaimNumber(claimNumber);
    props.onChange(event);
  };

  return (
    <InputText
      {...props}
      value={claimNumber}
      valueType="string"
      onChange={handleChange}
    />
  );
};

InputCaseNumber.propTypes = {
  onChange: PropTypes.func,
}

export default InputCaseNumber