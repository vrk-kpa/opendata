//Articles page search without login to service
describe('Articles search functionality', function() {
  // TODO: Haku tehdään sekä kirjautuneena että ilman sitä
  // TODO: Haun Teko

  // Without login
  //it('Articles search basic', function() {
  it('Visitor opens article list', function () {
    cy.visit("/");
    // Articles page
    cy.visit("/fi/artikkelit");
  })
  it('Visitor searches articles', function () {
    cy.get('#avoindata-articles-search-input').click();
    cy.get('#avoindata-articles-search-input').type('helsinki');
    cy.get('#avoindata-articles-search-btn').click();
  })


  // With login
  it('Logged in user opens article list', function () {
    cy.login_post_request('test-publisher', 'test-publisher');
    cy.visit("/");
    // Articles page
    cy.visit("/fi/artikkelit");
  })
  it('Logged in user searches articles', function () {
    const options = {scrollBehavior: 'center'};
    cy.get('#avoindata-articles-search-input').click(options);
    cy.get('#avoindata-articles-search-input').type('helsinki');
    cy.get('#avoindata-articles-search-btn').click(options);
  })

})
