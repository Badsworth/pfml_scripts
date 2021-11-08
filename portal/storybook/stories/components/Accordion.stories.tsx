import Accordion from "src/components/Accordion";
import AccordionItem from "src/components/AccordionItem";
import React from "react";

export default {
  title: "Components/Accordion",
  component: Accordion,
};

export const Default = () => (
  <Accordion>
    <AccordionItem heading="How we use your data">
      We’ll keep your information private as required by law. As a part of the
      application process, we may check the information you give with other
      state agencies.
    </AccordionItem>
    <AccordionItem heading="Applying for PFML">
      <React.Fragment>
        We need this information to:
        <ul className="usa-list">
          <li>Check your eligibility for coverage</li>
          <li>Determine your benefit amount </li>
          <li>Give you the best service possible</li>
        </ul>
      </React.Fragment>
    </AccordionItem>
  </Accordion>
);
