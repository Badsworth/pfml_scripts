Feature: Submit a Bonding Claim in which the claimant mails their HCP form at later time

  @portal
  Scenario: As a claimant, I should be able to start submitting a BGBM1 claim through the portal
    Given I begin to submit a "BGBM1" claim as a "financially eligible" employee
    And Part One of the claim has been submitted
    # Note: 
    # Feature currently being updated - https://lwd.atlassian.net/browse/CP-1259
    # And I have added payment information
    And I am on the claims "checklist" page
    When I click on the checklist button called "Upload identity document"
    Then I add my identity document "MA ID"
  
  @fineos
  Scenario: As a CSR (Savilix), I should be able to confirm that the HCP is missing
    Given I am logged into Fineos as a Savilinx user
    Given I should be able to find claim in Adjudication
    And I am on the tab "Documents"
    And the document "HCP" has been uploaded with "State Managed" business type
    Then I should find the "HCP" document
    Given I am on the tab "Absence Hub"
    When I click Adjudicate
    And I add paid benefits to the current case
    When I mark "State managed Paid Leave Confirmation" documentation as satisfactory
    And I mark "Identification Proof" documentation as satisfactory
    Then I should see that the claim's "Evidence" is "Satisfied"
    When I fill in the requested absence periods
    Then I should see that the claim's "Availability" is "Time Available"
    When I finish adjudication for the claim
    Then I should be able to approve the claim