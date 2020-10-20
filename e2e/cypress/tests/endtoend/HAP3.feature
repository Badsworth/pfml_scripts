Feature: Submit a medical claim that is happy, but financially ineligible, and is denied

  @portal
  Scenario: As a claimant, I should be able to start submitting a MedicalBasic claim through the portal
    Given I begin to submit a "HAP3" claim as a "financially ineligible" employee
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
    Then I add my identity document "MA ID"
    Given I am on the claims "checklist" page
    When I click on the checklist button called "Upload leave certification documents"
    Then I add my leave certification document "HCP"
    Given I am on the claims "checklist" page
    Then I should review and submit the application
    Given I am on the claims "review" page
    Then I should have agreed and successfully submitted the claim
    And I should be able to confirm claim was submitted successfully

  @fineos
  Scenario: As a CSR (Savilinx), I should be able to deny a claim based off financial ineligibility
    Given I search for the proper claim in Fineos
    When I click Adjudicate
    Given claim is financially ineligible
    Then I click Reject
    Given I am on the claim case page
    And claim is rejected
    When I click Deny
    Given I complete claim Denial for "Ineligible"
    Then I should confirm claim has been completed
