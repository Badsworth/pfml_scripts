export type UsefulClaimData = {
  id: string;
  scenario: string;
  first_name?: string | null;
  last_name?: string | null;
  tax_identifier?: string | null;
  employer_fein?: string | null;
};

export function getDataFromClaim(
  claim: GeneratedClaim | undefined
): UsefulClaimData {
  if (!claim) {
    throw new Error("No claim");
  }
  const { tax_identifier, employer_fein, first_name, last_name } = claim.claim;
  return {
    id: claim.id,
    scenario: claim.scenario,
    first_name,
    last_name,
    tax_identifier,
    employer_fein,
  };
}
