Feature: Financial Eligibility Can be Checked in FINEOS
    
  @fineos
  Scenario: I check a financially eligible claim in FINEOS
    # Given there is a new "financially eligible" claim
    Given I submit a "HAP1" claim directly to API as a "financially eligible" employee
    And I search for the proper claim in Fineos
    Then I see that financially eligibility is "Met"
  @fineos
  Scenario: I check a financially ineligible claim in FINEOS
    # Given there is a new "financially ineligible" claim
    Given I submit a "HAP1" claim directly to API as a "financially ineligible" employee
    And I search for the proper claim in Fineos
    Then I see that financially eligibility is "Not Met"

