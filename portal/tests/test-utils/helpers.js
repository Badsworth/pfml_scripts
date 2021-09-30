import BenefitsApplicationCollection from "../../src/models/BenefitsApplicationCollection";
import { MockBenefitsApplicationBuilder } from ".";

/**
 * Helper used by test to add benefits applications mocks
 * @param {Function} appLogicHook
 * @param {Array<BenefitsApplication>} claims
 * @param {Function} cb
 */
export const setupBenefitsApplications = (appLogicHook, claims, cb) => {
  if (!claims) {
    claims = [new MockBenefitsApplicationBuilder().create()];
  }
  appLogicHook.benefitsApplications.load = jest.fn();
  appLogicHook.benefitsApplications.loadAll = jest.fn();
  appLogicHook.benefitsApplications.hasLoadedAll = true;
  appLogicHook.benefitsApplications.benefitsApplications =
    new BenefitsApplicationCollection(claims);
  appLogicHook.benefitsApplications.hasLoadedBenefitsApplicationAndWarnings =
    jest.fn(() => Promise.resolve(true));
  if (cb) {
    cb(appLogicHook);
  }
};
