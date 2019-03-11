describe('Basic tests', function() {
  it('Opens frontpage!', function() {
    cy.visit("/");
  });

  // Opens pages, which don't require a certain dataset, resource, organization
  // or other item to exist. Only tests that the url doesn't return an error code
  it('Opens all kinds of various pages', function() {
    cy.visit("/data/dataset");
    cy.visit("/data/en_GB/dataset");
    cy.visit("/data/dataset?tags=test")
    cy.visit("/data/organization");
    cy.visit("/data/sv/organization");
    cy.visit("/data/showcase");
    cy.visit("/data/submit-showcase")
    cy.visit("/data/group");
    cy.request("/data/api/3");
    cy.visit("/artikkelit");
    cy.visit("/en/articles");
    cy.visit("/sv/artiklar")
    cy.visit("/opas");
    cy.visit("/en/guide");
    cy.visit("/sv/guide");
    cy.visit("fi/guide-search?search_api_fulltext=test");
    cy.visit("/user/register");
    cy.visit("/contact");
    cy.visit("/tapahtumat")
    cy.visit("/en/events");
    cy.visit("/sv/evenemanger");
  })
});

describe('Login page', function(){
  it('Logs in', function(){
    cy.login('admin', 'administrator');
  })
  it('Logs out', function(){
    cy.login_post_request('admin', 'administrator');
    cy.logout();
  })
});
