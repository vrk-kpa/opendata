//Artikkelit sivun hakuruutu (Flow muuttuu)
describe('Articles search functionality', function() {
    // TODO: Haku tehdään sekä kirjautuneena että ilman sitä
    // TODO: Haun Teko
  
    // Without login
    //it('Articles search basic', function() {
      it('Opens articles page!', function () {
        cy.visit("/");
        // Artikkelit 
        cy.visit("/fi/artikkelit");
      })
      it('Hae', function () {
        cy.get('#avoindata-articles-search-input').click();
        cy.get('#avoindata-articles-search-input').type('helsinki');
        cy.get('#avoindata-articles-search-btn').click();
      })
    })

    // With login
    it('Opens articles page!', function () {
        cy.login_post_request('test-publisher', 'test-publisher');
        cy.visit("/");
        // Artikkelit 
        cy.visit("/fi/artikkelit");
    })
    it('Hae', function () {
        cy.get('#avoindata-articles-search-input').click();
        cy.get('#avoindata-articles-search-input').type('helsinki');
        cy.get('#avoindata-articles-search-btn').click();
    })

    