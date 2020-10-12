Feature: Financial Eligibility Can be Checked in FINEOS
    
  @fineos
  Scenario: I check a financially eligible claim in FINEOS
    Given there is a new "financially eligible" claim
    And I search for the proper claim in Fineos
    Then I see that financially eligibility is "Met"
  @fineos
  Scenario: I check a financially ineligible claim in FINEOS
    Given there is a new "financially ineligible" claim
    And I search for the proper claim in Fineos
    Then I see that financially eligibility is "Not Met"

