import PortalSubmitter from "./PortalSubmitter";
import { SimulationClaim, SimulationExecutor } from "./types";

export default function createExecutor(
  submitter: PortalSubmitter
): SimulationExecutor {
  return async function execute(claim: SimulationClaim) {
    // This executor should:
    // * Create the claim using the API client.
    // * Update the claim using the API client.
    // * Final submission of the claim using the API client.

    // @Todo
    // * Uploading any documents that should be handled online.
    // * Moving any documents that should be handled offline to the proper directory.
    // console.log("herehrerhehre", claim.claim)

    submitter.submit(claim.claim);
    submitter.count++;
  };
}
