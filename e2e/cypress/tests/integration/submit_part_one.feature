Feature: Submit part one of a claim, without documents, and commence it in FINEOS

  @portal
  Scenario: As a claimant, I submit a HAP1 claim through the portal (part one)
    Given I begin the process to submit a "HAP1" claim
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

  @fineos
  Scenario: As a CSR (Savilinx), I should be able to commence intake on a HAP1 claim
    Given I am logged into Fineos as a Savilinx user
    Then I can commence intake on that claim