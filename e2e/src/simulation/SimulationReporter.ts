import SimulationStateTracker from "./SimulationStateTracker";
import type { SimulationClaim } from "./types";
import stringify from "csv-stringify";

async function buildData(
  state: SimulationStateTracker,
  claims: SimulationClaim[]
) {
  const recordPromises = claims.map(async (claim) => {
    const stateRecord = await state.get(claim.id);
    return {
      id: claim.id,
      scenario: claim.scenario,
      first_name: claim.claim.first_name,
      last_name: claim.claim.last_name,
      tax_identifier: claim.claim.tax_identifier,
      employer_fein: claim.claim.employer_fein,
      submitted: stateRecord?.time ?? "Never",
      caseNumber: stateRecord?.result,
      wages: claim.wages,
      error: stateRecord?.error,
    };
  });
  return await Promise.all(recordPromises);
}

export default async function stream(
  state: SimulationStateTracker,
  claims: SimulationClaim[]
): Promise<stringify.Stringifier> {
  const rows = await buildData(state, claims);
  const options = {
    header: true,
    columns: {
      id: "Unique ID",
      scenario: "Scenario",
      first_name: "First Name",
      last_name: "Last Name",
      tax_identifier: "SSN",
      employer_fein: "FEIN",
      caseNumber: "Fineos Case #",
      wages: "Yearly Wages",
      error: "Error Message",
    },
  };
  return stringify(rows, options);
}
