/**
 * @file Example template of various page components
 */
import Heading from "../../src/components/Heading";
import Lead from "../../src/components/Lead";
import Title from "../../src/components/Title";
import React from "react";

export default {
  title: "Templates|Content page",
};

export const Basic = () => (
  <React.Fragment>
    <Title>Title: We couldn’t find you in our records.</Title>
    <Lead>
      <strong>Lead</strong>: We didn’t find your name and SSN together in our
      records. You’re not eligible to take paid leave without a matching record.
    </Lead>

    <Lead>
      If you believe you are eligible for this program, call the Paid Family
      Leave Contact Center at (888) 888 - 8888. Then come back to create a
      claim.
    </Lead>

    <Heading level="2">Heading 2: Why can’t you find me?</Heading>

    <Heading level="3">Heading 3: You may not be contributing</Heading>
    <p>
      To be eligible for this program, you need to have payments into the paid
      leave fund. Your employer makes these payments for you every quarter. If
      there are no contributions, you won’t show up in our records.
    </p>

    <Heading level="3">
      Your information in our records might be incorrect
    </Heading>
    <ul className="usa-list">
      <li>
        There could have been an issue when your employer entered your
        information, such as misspelling your name.
      </li>
      <li>There could have been an issue when you entered your information.</li>
    </ul>
  </React.Fragment>
);
