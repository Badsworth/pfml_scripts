import { ConsentToDataSharing } from "src/pages/user/consent-to-data-sharing";
import { Props } from "storybook/types";
import React from "react";
import User from "src/models/User";

export default {
  title: "Pages/User/Consent to data sharing",
  component: ConsentToDataSharing,
};

export const Page = (
  args: Props<typeof ConsentToDataSharing> & { query: string }
) => {
  // @ts-expect-error ts-migrate(2554) FIXME: Expected 1 arguments, but got 0.
  let user = new User();
  if (args.query === "Employer Portal") {
    // @ts-expect-error ts-migrate(2741) FIXME: Property 'role_id' is missing in type '{ role_desc... Remove this comment to see the full error message
    user = new User({ roles: [{ role_description: "Employer" }] });
  }

  const appLogic = {
    users: {
      updateUser: () => {},
    },
  };

  // @ts-expect-error ts-migrate(2740) FIXME: Type '{ users: { updateUser: () => void; }; }' is ... Remove this comment to see the full error message
  return <ConsentToDataSharing appLogic={appLogic} user={user} />;
};

Page.argTypes = {
  query: {
    defaultValue: "Default",
    control: {
      type: "radio",
      options: ["Claimant Portal", "Employer Portal"],
    },
  },
};
