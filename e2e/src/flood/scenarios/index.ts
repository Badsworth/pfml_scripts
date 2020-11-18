import { StoredStep } from "../config";
import * as FineosClaimSubmit from "./FineosClaimSubmit.perf";
import * as PortalClaimSubmit from "./PortalClaimSubmit.perf";
import * as PortalRegistration from "./PortalRegistration.perf";
import * as LeaveAdminSelfRegistration from "./LeaveAdminSelfReg.perf";
import * as SavilinxAgent from "./SavilinxAgent.perf";
import * as DFMLOpsAgent from "./DFMLOpsAgent.perf";

export default [
  FineosClaimSubmit,
  PortalClaimSubmit,
  PortalRegistration,
  LeaveAdminSelfRegistration,
  SavilinxAgent,
  DFMLOpsAgent,
].reduce(
  (allScenarios, curr) => ({
    ...allScenarios,
    [curr.scenario]: curr.steps,
  }),
  {}
) as {
  [k: string]: StoredStep[];
};
