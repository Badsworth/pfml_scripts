Feature: Submit a medical claim with a mismatched SSN/ID

  @portal
  Scenario: As a claimant, I should be able to start submitting a GBR1 claim through the portal
    Given I begin the process to submit a "UNH3" claim
    When I click on the checklist button called "Verify your identity"
    Then I have my identity verified "normal"
    Given I am on the claims "checklist" page
    When I click on the checklist button called "Enter leave details"
    Then I start submitting the claim
    And I answer the pregnancy question
    And I answer the continuous leave question
    And I answer the reduced leave question
    And I answer the intermittent leave question
    Given I am on the claims "checklist" page
    When I click on the checklist button called "Enter employment information"
    Then I enter employer info
    Given I am on the claims "checklist" page
    When I click on the checklist button called "Report other leave, income, and benefits"
    Then I report other benefits
    Given I am on the claims "checklist" page
    When I click on the checklist button called "Review and confirm"
    Given I am on the claims "review" page
    Then I should have confirmed that information is correct
    Given I am on the claims "checklist" page
    When I click on the checklist button called "Add payment information"
    Then I add payment info
    Given I am on the claims "checklist" page
    When I click on the checklist button called "Upload identity document"
    Then I add my identity document
    Given I am on the claims "checklist" page
    When I click on the checklist button called "Upload leave certification documents"
    Then I add my leave certification documents
    Given I am on the claims "checklist" page
    Then I should review and submit the application
    Given I am on the claims "review" page
    Then I should have agreed and successfully submitted the claim
    And I should be able to return to the portal dashboard

  @fineos
  Scenario: As a CSR (Savilix), I should be able to confirm that an MA ID is not valid
    Given I search for the proper claim in Fineos
    And I am on the tab "Documents"
    And the document "MA ID" has been uploaded
    Then I should find the "MA ID" document
    Given I am on the tab "Absence Hub"
    When I click Adjudicate
    Given I am on the tab "Evidence"
    When I click Manage Evidence
    Then I should confirm evidence is "invalid due to mismatched ID and SSN"
    Given I am on the tab "Manage Request"
    Then I click Reject
    Given I am on the claim case page
    And claim is rejected
    When I click Deny
    Given I complete claim Denial for "Insufficient Certification"
    And I should confirm claim has been completed
