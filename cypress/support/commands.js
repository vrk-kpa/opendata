// ***********************************************
// This example commands.js shows you how to
// create various custom commands and overwrite
// existing commands.
//
// For more comprehensive examples of custom
// commands please read more here:
// https://on.cypress.io/custom-commands
// ***********************************************
//
//
// -- This is a parent command --
// Cypress.Commands.add("login", (email, password) => { ... })
//
//
// -- This is a child command --
// Cypress.Commands.add("drag", { prevSubject: 'element'}, (subject, options) => { ... })
//
//
// -- This is a dual command --
// Cypress.Commands.add("dismiss", { prevSubject: 'optional'}, (subject, options) => { ... })
//
//
// -- This is will overwrite an existing command --
// Cypress.Commands.overwrite("visit", (originalFn, url, options) => { ... })

Cypress.Commands.add('login_post_request', (username, password) => {
    
    cy.request({
        method: 'POST',
        url: '/user/login',
        form: true,
        body: {
            name: username,
            pass: password,
            form_id: 'user_login_form'
        }
    });
})

Cypress.Commands.add('login', (username, password) => {

    cy.visit('/user/login');
    
    cy.get('input[name=name]').type(username);
    cy.get('input[name=pass]').type(password);
    cy.get('#edit-submit').click();

    cy.url().should('include', '/fi/user');

    cy.getCookies().should('have.length', 1).then((cookies) => {
        expect(cookies[0]).to.have.property('name').to.match(/^SESS/);
    })
});

Cypress.Commands.add('logout', () => {
    cy.visit('/user/logout');

    cy.url().should('eq', Cypress.config().baseUrl + '/fi');
    cy.getCookies().should('have.length', 0);
})
  
    