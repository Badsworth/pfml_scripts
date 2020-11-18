Feature: Submit a bonding (Out of State) claim and assert adjucation

  @portal
  Scenario: As an OUT OF STATE claimant, I should be able to submit a BONDING claim (BHAP2) through the portal
    Given I begin to submit a "BHAP2" claim as a "financially eligible" employee
    And Part One of the claim has been submitted
    And I have added payment information
    And I am on the claims "checklist" page
    When I click on the checklist button called "Upload identity document"
    Then I add my identity document "MA ID"
    When I click on the checklist button called "Upload leave certification documents"
    Then I add my leave certification document "ADOPTION"
    Given I am on the claims "checklist" page
    Then I should review and submit the application
    Given I am on the claims "review" page
    Then I should have agreed and successfully submitted the claim
    And I should be able to confirm claim was submitted successfully

  @fineos
  Scenario: As a CSR (Savilinx), I should be able find claim in Adjudication
    Given I am logged into Fineos as a Savilinx user
    Then I should be able to find claim in Adjudication