import { Browser } from "@flood/element";
import Approve from "./ApproveClaim";
import Deny from "./DenyClaim";

export default async (browser: Browser, data: unknown): Promise<void> => {
  const decideStep = Math.random() > 0.5 ? Approve : Deny;
  await decideStep(browser, data);
};
