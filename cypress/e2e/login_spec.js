describe('Login page tests', function(){

    beforeEach(function(){
      cy.visit('/');
    });
  
      it('Admin Login', function(){
        cy.login('admin', 'administrator');
        cy.location('pathname').should('contain', `/data/fi/user/admin`)
      });
      
      it('Admin Logout', function(){
        cy.login('admin', 'administrator');
        cy.location('pathname').should('contain', `/data/fi/user/admin`);
        cy.logout();
        cy.location('pathname').should('not.contain', `/data/fi/user/admin`);
      });
  
      it('User Login', function(){
        cy.login('test-user', 'test-user');
        cy.location('pathname').should('contain', `/data/fi/user/test-user`)
      });
      
      it('User Logout', function(){
        cy.login('test-user', 'test-user');
        cy.location('pathname').should('contain', `/data/fi/user/test-user`)
        cy.logout();
        cy.location('pathname').should('not.contain', `/data/fi/user/test-user`);
      });
  
  
    });
