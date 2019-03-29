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
  

// This function only fills the fields according to given parameters. 
// Other actions, such as editing URL and clicking buttons are handled by
// other more specififc functions, because of the small differences between
// forms. 
Cypress.Commands.add('fill_form_fields', (form_data) => {
  Object.keys(form_data).forEach(function(field_selector){
    var field_value = form_data[field_selector];
    cy.get(field_selector).type(field_value);
  });  
})


// Creates a new dataset filling both dataset and resource forms
Cypress.Commands.add('create_new_dataset', (dataset_name, dataset_form_data, resource_form_data) => {
  
  // Default values for dataset and resource forms
  if (dataset_form_data === undefined) {
    dataset_form_data = {
      "#field-title_translated-fi": dataset_name,
      '#field-notes_translated-fi': 'Dataset test description',
      '#s2id_autogen1': 'test_keyword {enter}',
      '#field-maintainer': 'test maintainer',
      '#field-maintainer_email': 'test.maintainer@example.com'
    }
  }
  if (resource_form_data === undefined) {
    resource_form_data = {
      "#field-name_translated-fi": 'test data'
    }
  }

  //Dataset form
  cy.get('a[href="/data/fi/dataset/new"]').click(); 
  cy.get('.slug-preview button').contains('Muokkaa').click();
  cy.get('#field-name').type(dataset_name);
  cy.fill_form_fields(dataset_form_data);
  cy.get('button[name=save]').click();

  //Resource form, filled with just the name
  cy.fill_form_fields(resource_form_data);
  cy.get('button[name=save]').contains('Valmis').click(); 
  cy.url().should('include', `/data/fi/dataset/${dataset_name}`);
})

// Edits an existing dataset
Cypress.Commands.add('edit_dataset', (dataset_name, dataset_form_data) => {

  if (dataset_form_data === undefined) {
    dataset_form_data = {
      "#field-title_translated-fi": 'edit',
    }
  }
  cy.get(`a[href='/data/fi/dataset/edit/${dataset_name}']`).click();
  cy.fill_form_fields(dataset_form_data)
  cy.get('button[name=save]').click();
  cy.get('.dataset-title-column').contains(dataset_name+'edit');
})

// Deletes a dataset and verifies that it is not found in the search anymore
// It expects a random_id string as a parameter, which is used to verify that
// the dataset is deleted. This random_id should also be part of the dataset_name
Cypress.Commands.add('delete_dataset', (dataset_name, random_id) => {
  cy.get(`a[href='/data/fi/dataset/edit/${dataset_name}']`).click();
  cy.get('.form-actions').contains('Poista').click();
  cy.contains('Haluatko varmasti poistaa tietoaineiston');
  cy.get('body').find('.btn').contains('Vahvista').click();
  cy.get('.search-input .search').type(random_id + '{enter}');
  cy.get('.dataset-list').should('not.exist');
  cy.contains("ei löytynyt tietoaineistoja");
})


// Creates a new showcase filling both showcase and resource forms
Cypress.Commands.add('create_new_showcase', (showcase_name, showcase_form_data) => {
  
  // Default values for showcase
  if (showcase_form_data === undefined) {
    showcase_form_data = {
      "#field-title": showcase_name,
      '#field-notes_translated-fi': 'Dataset test description',
      '#s2id_autogen1': 'test_keyword {enter}',
      '#field-author': 'test author'
    }
  }

  // Showcase form
  cy.get('a[href="/data/fi/showcase/new"]').click(); 
  cy.get('.slug-preview button').contains('Muokkaa').click();
  cy.get('#field-name').type(showcase_name);
  cy.fill_form_fields(showcase_form_data);
  cy.get('button[name=save]').click();

  // Datasets form
  cy.get(`article a[href="/data/fi/showcase/${showcase_name}"]`).click(); 
  cy.url().should('include', `/data/fi/showcase/${showcase_name}`);
})

// Edits an existing showcase
Cypress.Commands.add('edit_showcase', (showcase_name, showcase_form_data) => {

  if (showcase_form_data === undefined) {
    showcase_form_data = {
      "#field-title": 'edit',
    }
  }
  cy.get(`a[href='/data/fi/showcase/edit/${showcase_name}']`).click();
  cy.fill_form_fields(showcase_form_data)
  cy.get('button[name=save]').click();
  cy.get('.page-heading').contains(showcase_name+'edit');
})

// Deletes a showcase and verifies that it is not found in the search anymore
// It expects a random_id string as a parameter, which is used to verify that
// the showcase is deleted. This random_id should also be part of the showcase_name
Cypress.Commands.add('delete_showcase', (showcase_name, random_id) => {
  cy.get(`a[href='/data/fi/showcase/edit/${showcase_name}']`).click();
  cy.get('.form-actions').contains('Poista').click();
  cy.contains('Haluatko varmasti poistaa tietoaineiston');
  cy.get('body').find('.btn').contains('Vahvista').click();
  cy.get('.search-input .search').type(random_id + '{enter}');
  cy.get('.showcase-list').should('not.exist');
  cy.contains("ei löytynyt tietoaineistoja");
})

Cypress.Commands.add('reset_db', () => {
    if (Cypress.env('resetDB') === true){
      cy.exec('npm run reset:db');
      cy.exec("vagrant ssh -c  \'sudo /usr/lib/ckan/default/bin/paster --plugin=ckan search-index clear --config=/etc/ckan/default/test.ini\'", {timeout: 120*1000});
    }
});
