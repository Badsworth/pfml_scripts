Feature: Submit an INTERMITTENT LEAVE bonding claim and adjucation approval - BHAP9

  @portal
  Scenario: As a claimant, I should be able to submit a claim (BHAP9) through the portal
    Given I begin to submit a "BHAP9" claim as a "financially eligible" employee
    When I am the "existing" claimant visiting the portal
    Then I continue creating the claim
    When I have submitted all parts of the claim
