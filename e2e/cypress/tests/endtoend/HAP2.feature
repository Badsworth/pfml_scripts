Feature: Submit and accept HAP2 claim: Simple claim, out of state resident

  @portal
  Scenario: As a claimant, I should be able to submit a claim (HAP2) through the portal
    Given I begin the process to submit a "HAP2" claim
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
    Then I add my identity document "OOS ID"
    Given I am on the claims "checklist" page
    When I click on the checklist button called "Upload leave certification documents"
    Then I add my leave certification documents
    Given I am on the claims "checklist" page
    Then I should review and submit the application
    Given I am on the claims "review" page
    Then I should have agreed and successfully submitted the claim
    And I should be able to return to the portal dashboard

  @fineos
  Scenario: As a CSR (Savilinx), I should be able to Approve a HAP2 claim submission
    Given I am logged into Fineos as a Savilinx user
    And I am viewing the previously submitted claim
    When I start adjudication for the claim
    And I add paid benefits to the current case
    Then I should see that the claim's "Eligibility" is "Met"
    When I mark "State Managed Paid Leave Confirmation" documentation as satisfactory
    And I mark "Identification Proof" documentation as satisfactory
    Then I should see that the claim's "Evidence" is "Satisfied"
    When I fill in the requested absence periods
    Then I should see that the claim's "Availability" is "Time Available"
    When I finish adjudication for the claim
    Then I should be able to approve the claim