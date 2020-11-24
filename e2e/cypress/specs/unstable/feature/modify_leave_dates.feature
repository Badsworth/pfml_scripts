Feature: Leave Dates can be modifed for an already submitted claim
    
  @fineos
  Scenario: As a CSR rep I can modify leave dates for a specific claim in Fineos
    Given I submit a "BHAP1" claim directly to API as a "financially eligible" employee
    And I search for the proper claim in Fineos
    Then I see that financially eligibility is "Met"
    When I start adjudication for the claim
    Given I am on the tab "Request Information"
    Then I should modify leave dates for the requested time off