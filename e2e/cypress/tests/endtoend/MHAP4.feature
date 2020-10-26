Feature: Submit a REDUCED LEAVE medical claim and adjucation approval - MHAP4

  @portal
  Scenario: As a claimant, I should be able to submit a claim (MHAP4) through the portal
    Given I begin to submit a "MHAP4" claim as a "financially eligible" employee
    When I have submitted all parts of the claim

