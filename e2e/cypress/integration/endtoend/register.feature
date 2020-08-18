Feature: Register new account

  @ignore
  @setFeatureFlags
  @catchStatusError
  Scenario: As a portal user, I should be able to register a new account
    Given I have an application to submit
    And I am an anonymous user on the portal homepage
    When I submit the account registration form
    Then I should be able to register a new account
