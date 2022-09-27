describe('Test contact page', function () {
    it('Sending feedback should succeed', function () {
      cy.visit('/contact');
      cy.get('#edit-name').type("Some name");
      cy.get('#edit-mail').type('foo@example.com');
      cy.get('#edit-subject-0-value').type('Some subject');
      cy.get('#edit-message-0-value').type('Some content for feedback');
      cy.get('#edit-submit').click();
      cy.get('.messages__wrapper').contains('Viestisi on lähetetty. Vastaamme siihen mahdollisimman pian.')
    });
  
    // Feedback with urls is currently being counted as spam, skip for now
    it.skip('Sending feedback containing site url should succeed', function () {
      cy.visit('/contact');
      cy.get('#edit-name').type("Some name");
      cy.get('#edit-mail').type('foo@example.com');
      cy.get('#edit-subject-0-value').type('Some subject');
      cy.get('#edit-message-0-value').type('This content contains url to site https://www.avoindata.fi');
      cy.get('#edit-submit').click();
      cy.get('.messages__wrapper').contains('Your message has been sent.')
    });
  
    it('Sending feedback containing external url should fail', function () {
      cy.visit('/en/contact');
      cy.get('#edit-name').type("Some name");
      cy.get('#edit-mail').type('foo@example.com');
      cy.get('#edit-subject-0-value').type('Some subject');
      cy.get('#edit-message-0-value').type('This content contains url to external site http://example.com');
      cy.get('#edit-submit').click();
      cy.get('.messages__wrapper').children('div').should('have.class', 'alert-danger').contains('spam content')
    });
});
