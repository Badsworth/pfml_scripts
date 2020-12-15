Feature: Claim has started notification

  @fineos
  Scenario: I want to confirm "claim has started" notification has been triggered
    Given I submit a "BHAP1" claim directly to API as a "financially eligible" employee
    And I search for the proper claim in Fineos
    Given I am on the tab "Documents"
    Then I should find the "MA ID" document
    And I should find the "FOSTER" document
    Given I am on the tab "Absence Hub"
    When I start adjudication for the claim
    Then I should see that the claim's "Eligibility" is "Met"
    And I mark "BHAP1" "State managed Paid Leave Confirmation" documentation as satisfactory
    And I mark "BHAP1" "Identification Proof" documentation as satisfactory
    Then I should see that the claim's "Evidence" is "Satisfied"
    Then I accept claim updates
    Given I am on the tab "Outstanding Requirements"
    Then I should find the "Employer Confirmation" document