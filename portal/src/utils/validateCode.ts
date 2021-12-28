function validateCode(code?: string) {
  if (!code) {
    return {
      field: "code",
      type: "required",
    };
  } else if (!code.match(/^\d{6}$/)) {
    return {
      field: "code",
      type: "pattern", // matches same type as API regex pattern validations
    };
  }
}

export default validateCode;
