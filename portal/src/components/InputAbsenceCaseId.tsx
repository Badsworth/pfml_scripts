import InputText, { InputTextProps } from "./core/InputText";
import React from "react";

interface InputAbsenceCaseIdProps extends InputTextProps {
  onChange: React.ChangeEventHandler<HTMLInputElement>;
}

const pattern = /^([a-z]+)-?([\d]+)-?([a-z]+)-?([\d]+)$/i;
const trailingPeriodPattern = /\.$/;

function InputAbsenceCaseId(props: InputAbsenceCaseIdProps) {
  const transformValue = (value: string) => {
    let transformedValue = value.toUpperCase().replace(/\s/g, "");
    transformedValue = transformedValue.replace(pattern, "$1-$2-$3-$4");
    transformedValue = transformedValue.replace(trailingPeriodPattern, "");
    return transformedValue;
  };

  const handleBlur = (originalEvent: React.FocusEvent<HTMLInputElement>) => {
    const target = originalEvent.target.cloneNode(true) as HTMLInputElement;
    target.value = transformValue(target.value);
    props.onChange({ ...originalEvent, target });
  };

  return <InputText {...props} onBlur={handleBlur} />;
}

export default InputAbsenceCaseId;
