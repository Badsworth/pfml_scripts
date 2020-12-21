Feature: Submit a <Scenario> claim directly to API and check for RMV Identification Status

  @fineos
  Scenario: I generate and submit a claim directly to the API and then check RMV ID Status
    Given I submit a "BHAP11ID" claim directly to API as a "financially eligible" employee
    And I am logged into Fineos as a Savilinx user
    Then I should be able to find claim in Adjudication
    And I confirm proper RMV ID status as "fraud"