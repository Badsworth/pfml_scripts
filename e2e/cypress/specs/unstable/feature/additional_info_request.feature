Feature: A CSR rep should be able to request additional information in the following cases
  - Incomplete applications
  - Applications with insufficient evidence
  - Applications with illegible evidence

  @fineos
  Scenario: As a tester - I can generate and submit a claim directly to the API
    Given I submit a "BHAP1" claim directly to API as a "financially eligible" employee
    And I search for the proper claim in Fineos
    When I start adjudication for the claim
    And I request additional information from the claimant
    Given I search for the proper claim in Fineos
    Then I add a note