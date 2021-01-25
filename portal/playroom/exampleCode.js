/**
 * @type {string}
 * Default code snippet displayed when Playroom is first opened. Useful
 * as a starting point, especially for folks unfamiliar with the codebase.
 */
module.exports = `
<Title>Page title</Title>
<Lead>Page lead text.</Lead>
<p>Page body text.</p>

<Heading level="2">Form components</Heading>

<InputText label="What's your name?" hint="Enter as it is on your ID." />

<InputDate
  label="What's your birthdate?"
  hint="We need this info to verify your identity."
  example="For example 09/20/1980"
  monthLabel="Month"
  dayLabel="Day"
  yearLabel="Year"
/>

<InputChoiceGroup
  label="Do you have a Social Security Number?"
  type="radio"
  choices={[
    {
      label: "Yes",
    },
    {
      label: "No",
    },
  ]}
/>

<Button className="margin-top-5">Save and continue</Button>

`;
