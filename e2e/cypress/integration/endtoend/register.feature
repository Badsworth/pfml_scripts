Feature: Register new account

  @setFeatureFlags
  @catchStatusError
  Scenario: As a portal user, I should be able to register a new account
    Given I am an anonymous user on the portal homepage
    When I submit the account registration form
    Then I should be able to register a new account
    And I should be able to log in
