import Fieldset from "src/components/Fieldset";
import FormLabel from "src/components/FormLabel";
import InputText from "src/components/InputText";
import QuestionPage from "src/components/QuestionPage";
import React from "react";

export default {
  title: "Templates/Question page",
  component: QuestionPage,
};

const sampleRoute = "/create-claim/address";
const sampleTitle = "Who is taking leave";

export const WithLegend = () => (
  <QuestionPage title={sampleTitle} nextPage={sampleRoute} onSave={() => {}}>
    <InputText
      name="ssn"
      label="What's your Social Security Number?"
      hint="Don't have an SSN? Use your Individual Taxpayer Identification Number (ITIN)."
    />
  </QuestionPage>
);

export const WithFieldset = () => (
  <QuestionPage title={sampleTitle} nextPage={sampleRoute} onSave={() => {}}>
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
