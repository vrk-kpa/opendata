// Quides page search with and without login to service
describe('Guides search functionality', function() {
  // TODO: Haku tehdään sekä kirjautuneena että ilman sitä
  // TODO: Haun Teko

  // Without login
  //it('Guides search basic', function() {
  it('Visitor opens guide front page', function () {
    cy.visit("/");
    cy.visit("/fi/opas");
  })
  
  // With login
  it('Logged in user opens guide front page', function () {
    cy.login_post_request('test-publisher', 'test-publisher');
    cy.visit("/");
    cy.visit("/fi/opas");
  })
})
