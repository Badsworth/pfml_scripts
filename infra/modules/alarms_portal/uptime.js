/**
 * This synthetic check lives in Terraform.
 *
 * Do not edit this script in New Relic.
 */
const URI = "${uri}"; // Variable passed from Terraform

/**
 * Test a login attempt. This doesn't enter valid account information,
 * but it helps assert that the Portal is not behind a maintenance window,
 * and that a request is at least being successfully sent to Cognito.
 */
$browser
  .get(URI)
  .then(() => $browser.findElement($driver.By.linkText("Log in")).click())
  .then(() =>
    $browser
      .findElement($driver.By.name("username"))
      .sendKeys("new-relic-synthetic@example.com")
  )
  .then(() =>
    $browser.findElement($driver.By.name("password")).sendKeys("test")
  )
  .then(() =>
    $browser.findElement($driver.By.xpath("//button[@type='submit']")).click()
  )
  .then(() =>
    // We expect Cognito to prevent the login since the login credentials are fake.
    // We can't reliably expect a valid login to be successful, because Cognito
    // ends up blocking scripted logins when performed through a New Relic synthetic.
    $browser.waitForAndFindElement(
      $driver.By.xpath("//h2[text()='An error occurred']")
    )
  );
