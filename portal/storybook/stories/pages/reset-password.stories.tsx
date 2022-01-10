import { Props } from "types/common";
import React from "react";
import ResetPassword from "src/pages/reset-password";
import useMockableAppLogic from "lib/mock-helpers/useMockableAppLogic";

export default {
  title: "Pages/Auth/Reset Password",
  component: ResetPassword,
  argTypes: {
    scenario: {
      control: {
        type: "radio",
        options: ["With cached email", "Without cached email"],
      },
    },
  },
  args: {
    scenario: "With cached email",
  },
};

export const Page = (
  args: Props<typeof ResetPassword> & { scenario: string }
) => {
  const authData = {
    resetPasswordUsername:
      args.scenario === "With cached email" ? "test@example.com" : undefined,
  };

  const appLogic = useMockableAppLogic({
    auth: {
      authData,
    },
  });

  return <ResetPassword appLogic={appLogic} />;
};
