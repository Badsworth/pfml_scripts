import { AppLogic } from "../../src/hooks/useAppLogic";
import BenefitsApplication from "../../src/models/BenefitsApplication";
import BenefitsApplicationCollection from "../../src/models/BenefitsApplicationCollection";
import { MockBenefitsApplicationBuilder } from ".";

/**
 * Helper used by test to add benefits applications mocks
 */
export const setupBenefitsApplications = (
  appLogicHook: AppLogic,
  claims?: BenefitsApplication[],
  cb?: (appLogic: AppLogic) => void
) => {
  if (!claims) {
    claims = [new MockBenefitsApplicationBuilder().create()];
  }
  appLogicHook.benefitsApplications.load = jest.fn();
  appLogicHook.benefitsApplications.loadPage = jest.fn();
  appLogicHook.benefitsApplications.isLoadingClaims = false;
  appLogicHook.benefitsApplications.benefitsApplications =
    new BenefitsApplicationCollection(claims);
  appLogicHook.benefitsApplications.hasLoadedBenefitsApplicationAndWarnings =
    jest.fn(() => true);
  if (cb) {
    cb(appLogicHook);
  }
};
