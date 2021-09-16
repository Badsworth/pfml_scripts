import Accordion from "../../src/components/Accordion";
import AccordionItem from "../../src/components/AccordionItem";
import React from "react";
import { render } from "@testing-library/react";

describe("Accordion", () => {
  it("renders an AccordionItem for each item", () => {
    const { container } = render(
      <Accordion>
        <AccordionItem heading="Heading 1">Body 1</AccordionItem>
        <AccordionItem heading="Heading 2">
          <p>Body 2</p>
        </AccordionItem>
      </Accordion>
    );

    expect(container.firstChild).toMatchSnapshot();
  });
});
