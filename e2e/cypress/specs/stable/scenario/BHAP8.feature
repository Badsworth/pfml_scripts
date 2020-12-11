Feature: Submit a REDUCED LEAVE bonding claim and adjucation approval - BHAP8

  @portal
  Scenario: As a claimant, I should be able to submit a Reduced Leave claim (BHAP8) through the portal
    Given I begin to submit a "BHAP8" claim as a "financially eligible" employee
    When I am the "existing" claimant visiting the portal
    Then I continue creating the claim
    When I have submitted all parts of the claim

