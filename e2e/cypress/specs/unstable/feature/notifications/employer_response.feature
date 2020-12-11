Feature: Mark evidence received on a claim in FINEOS and employer responds by denying claim

  @portal
  Scenario: As a claimant, I should be able to submit a claim (BHAP1) through the portal
    Given I begin to submit a "BHAP1" claim as a "financially eligible" employee
    When I click on the checklist button called "Verify your identity"
    Then I have my identity verified "normal"
    Given I am on the claims "checklist" page
    When I click on the checklist button called "Enter employment information"
    Then I enter employer info
    Given I am on the claims "checklist" page
    When I click on the checklist button called "Enter leave details"
    Then I start submitting the claim
    And I enter "Foster Care" date
    And I answer the continuous leave question
    And I answer the reduced leave question
    And I answer the intermittent leave question
    # Note:
    # Feature has been removed until soft launch (2nd Dec 2020)
    # Given I am on the claims "checklist" page
    # When I click on the checklist button called "Report other leave, income, and benefits"
    # Then I report other benefits
    Given I am on the claims "checklist" page
    When I click on the checklist button called "Review and confirm"
    And I confirm that I am an eligible parent
    Given I am on the claims "review" page
    Then I should have confirmed that information is correct
    Given I am on the claims "checklist" page
    When I click on the checklist button called "Add payment information"
    Then I add payment info
    Given I am on the claims "checklist" page
    When I click on the checklist button called "Upload identity document"
    Then I add my identity document "MA ID"
    When I click on the checklist button called "Upload leave certification documents"
    Then I add my leave certification document "FOSTER"
    Given I am on the claims "checklist" page
    Then I should review and submit the application
    Given I am on the claims "review" page
    Then I should have agreed and successfully submitted the claim
    And I should be able to confirm claim was submitted successfully

    When I log out
    Given I am a Leave Admin for the submitted applications
    And I am on the New Application page
    And I confirm I am the right person to respond
    And I review the application: I "do not" suspect fraud, employee gave "insufficient" notice, and I "deny" the claim

  # @portal
  # Temporarily suspending notification testing until mailbox is whitelisted
  # Scenario: An employer should receive a notification to respond to claim and be able to deny it
  #   Then I should receive a "employer response" notification

