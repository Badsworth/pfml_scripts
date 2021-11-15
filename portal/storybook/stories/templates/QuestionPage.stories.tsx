import Fieldset from "src/components/core/Fieldset";
import FormLabel from "src/components/core/FormLabel";
import InputText from "src/components/core/InputText";
import QuestionPage from "src/components/QuestionPage";
import React from "react";

export default {
  title: "Templates/Question page",
  component: QuestionPage,
};

const sampleTitle = "Verify your identity";

export const WithLegend = () => (
  // @ts-expect-error ts-migrate(2322) FIXME: Type '() => void' is not assignable to type '() =>... Remove this comment to see the full error message
  <QuestionPage title={sampleTitle} onSave={() => {}}>
    <InputText
      name="ssn"
      label="What's your Social Security Number?"
      hint="Don't have an SSN? Use your Individual Taxpayer Identification Number (ITIN)."
    />
  </QuestionPage>
);

export const WithFieldset = () => (
  // @ts-expect-error ts-migrate(2322) FIXME: Type '() => void' is not assignable to type '() =>... Remove this comment to see the full error message
  <QuestionPage title={sampleTitle} onSave={() => {}}>
    <Fieldset>
      <FormLabel component="legend" hint="Some text here about names">
        Input your name here
      </FormLabel>
      <InputText name="firstName" label="First name" smallLabel />
      <InputText
        name="middleName"
        label="Middle name"
        optionalText="(optional)"
        smallLabel
      />
    </Fieldset>
  </QuestionPage>
);
