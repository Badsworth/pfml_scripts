Feature: Submit a medical claim and adjucation approval - MHAP1

  @portal
  Scenario: As a claimant, I should be able to submit a claim (MHAP1) through the portal
    Given I begin to submit a "MHAP1" claim as a "financially eligible" employee
    When I am the "existing" claimant visiting the portal
    Then I continue creating the claim
    When I click on the checklist button called "Verify your identity"
    Then I have my identity verified "normal"
    Given I am on the claims "checklist" page
    When I click on the checklist button called "Enter employment information"
    Then I enter employer info
    Given I am on the claims "checklist" page
    When I click on the checklist button called "Enter leave details"
    Then I start submitting the claim
    And I answer the pregnancy question
    And I answer the continuous leave question
    And I answer the reduced leave question
    And I answer the intermittent leave question
    # Given I am on the claims "checklist" page
    # When I click on the checklist button called "Report other leave, income, and benefits"
    # Then I report other benefits
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
  @ignore
  @fineos
  Scenario: As a CSR (Savilinx), I should be able to Approve a MHAP1 claim submission
    Given I am logged into Fineos as a Savilinx user
    Then I should be able to find claim in Adjudication
    And I should confirm proper tasks have been created
    When I start adjudication for the claim
    Then I should see that the claim's "Eligibility" is "Met"
    When I mark "BHAP1" "State managed Paid Leave Confirmation" documentation as satisfactory
    And I mark "BHAP1" "Identification Proof" documentation as satisfactory
    Then I should see that the claim's "Evidence" is "Satisfied"
    When I fill in the requested absence periods
    Then I should see that the claim's "Availability" is "Time Available"
    When I finish adjudication for the claim
    Then I should be able to approve the claim



