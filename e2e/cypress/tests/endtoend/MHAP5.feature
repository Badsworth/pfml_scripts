Feature: Submit an INTERMITTENT LEAVE medical claim and adjucation approval - MHAP5

  @portal
  Scenario: As a claimant, I should be able to submit a claim (MHAP5) through the portal
    Given I begin to submit a "MHAP5" claim as a "financially eligible" employee
    When I have submitted all parts of the claim
