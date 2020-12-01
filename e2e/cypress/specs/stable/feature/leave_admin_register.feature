Feature: Register new paid leave admin account from the employer portal.

  @portal
  Scenario: As a portal user, I should be able to register a employer account
    Given I am an anonymous employer user on the portal homepage
    When I submit the employer registration form
    And I log into the employer portal
    And I accept the terms of service
    Then I should be logged in

# @todo: This functionality was removed prior to the 12/2 launch to address load issues.
#  @fineos
#  Scenario: As a CSR (Savilinx), I should be able to locate the point of contact on the employer page
#    Given I am logged into Fineos as a Savilinx user
#    Then I should be able to find employer page
#    And I should be able to find the POC
