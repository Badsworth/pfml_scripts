import { chance, SimulationGenerator } from "../simulate";
import { LSTDataConfig } from "../../commands/flood/common";
import * as LSTGenerators from "./pilot4LST";

export const customizable = true;
export default function (config: LSTDataConfig[]): SimulationGenerator {
  return chance(
    config.reduce((total, cfg) => {
      switch (cfg.scenario) {
        case "PortalClaimSubmit":
        case "FineosClaimSubmit":
          const isPortal = cfg.scenario === "PortalClaimSubmit";
          const eligibleScenario = isPortal
            ? LSTGenerators.BHAP1
            : LSTGenerators.FBHAP1;
          const ineligibleScenario = isPortal
            ? LSTGenerators.BHAP4
            : LSTGenerators.FBHAP4;
          if (cfg.eligible === 100) {
            total.push([cfg.chance, eligibleScenario]);
          } else {
            const elgRatio = (cfg.eligible as number) / 100;
            total.push([Math.round(cfg.chance * elgRatio), eligibleScenario]);
            total.push([
              Math.round(cfg.chance * (1 - elgRatio)),
              ineligibleScenario,
            ]);
          }
          break;
        case "LeaveAdminSelfRegistration":
          total.push([cfg.chance, LSTGenerators.LeaveAdminSelfReg]);
          break;
        case "SavilinxAgent":
          total.push([cfg.chance, LSTGenerators.SavilinxAgent]);
          break;
        default:
          total.push([cfg.chance, LSTGenerators.BHAP1]);
          break;
      }
      return total;
    }, [] as [number, SimulationGenerator][])
  );
}
