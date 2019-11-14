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
  // Check that authentication cookie doesn't exist anymore
  cy.getCookies().each((cookie) => {
    if(cookie.name){
      expect(cookie).to.have.property('name').to.not.match(/^SESS/);
    }
  })
})


/**
 * @description
 * This function only fills the fields according to given parameters.
 * Other actions, such as editing URL and clicking buttons are handled by
 * other more specific functions, because of the small differences between
 * forms.
 *
 * @typedef FormFillOptions
 * @type {Object}
 * @property {string} [value] - The field value
 * @property {'select' | 'check'} [type] - The type of method to use to populate field, default to type
 * @property {boolean} [force] - Adds option force to field
 *
 * @typedef {{[k: string]: string | FormFillOptions}} FormFillValues
 *
 * @param {FormFillValues[]} form_data
 * The data to populate the form with
 * Keys are used as selectors to select the right field
 * Values are either string or object
*/
Cypress.Commands.add('fill_form_fields', (form_data) => {
    Object.keys(form_data).forEach(function(field_selector){
        const field_value = form_data[field_selector];
        const field = cy.get(field_selector)
        if (field_value && typeof field_value === 'object') {
            const options = { force: field_value.force ? field_value.force : false };
            switch(field_value.type) {
                case 'select':
                    field.select(field_value.value, options)
                    break;
                case 'check':
                    field.check(options)
                    break;
                default:
                    field.type(field_value.value, options)
            }
        } else {
            field.type(field_value);
        }
    });
})

Cypress.Commands.add('create_new_organization', (organization_name, organization_form_data) => {
  // Default values for organization form
  if (!organization_form_data) {
    organization_form_data = {
      "#field-title_translated-fi": organization_name
    }
  }
  cy.visit("/data/fi/organization");
  cy.get('a[href="/data/fi/organization/new"]').click();
  cy.get('.slug-preview button').contains('Muokkaa').click();
  cy.fill_form_fields(organization_form_data);
  cy.get('button[name="save"]').click();
  cy.url().should('include', `/data/fi/organization/${organization_name}`);
})

Cypress.Commands.add('approve_organization', (organization_id) => {
  // Approves a previously created organization
  cy.request({
    method: 'POST',
    url: "/data/fi/ckan-admin/organization_management",
    form: true,
    body: {
      'org_id': organization_id,
      'approval_status': 'approved'
    }
  });
})

Cypress.Commands.add('create_new_dataset', (dataset_name, dataset_form_data, resource_form_data, parent_organization) => {

  // Default values for dataset and resource forms
  if (!dataset_form_data) {
    dataset_form_data = {
      "#field-title_translated-fi": dataset_name,
      '#field-notes_translated-fi': 'Dataset test description',
      '#s2id_autogen1': 'test_keyword {enter}',
      '#field-maintainer': 'test maintainer',
      '#field-maintainer_email': 'test.maintainer@example.com'
    }
  }
  if (!resource_form_data) {
    resource_form_data = {
      "#field-name_translated-fi": 'test data',
      '#field-image-url': 'http://example.com'
    }
  }

  //Dataset form
  cy.get('#second-navbar a[href="/data/fi/dataset"]').click();
  cy.get('a[href="/data/fi/dataset/new"]').click();
  cy.get('.slug-preview button').contains('Muokkaa').click();
  cy.get('#field-name').type(dataset_name);
  cy.fill_form_fields(dataset_form_data);

  // The selector field is hidden so force is required.
  // The visible UI element for selecting the organization is not as easy to use with cypress
  if (parent_organization) {
    cy.get("#field-organizations").select(parent_organization, {force: true});
  }

  // Make dataset public instead of private
  cy.get("#field-private").select("False").should('have.value', 'False');

  cy.get('button[name=save]').click();

  //Resource form, filled with just the name
  cy.contains('a', 'Linkki').click()
  cy.fill_form_fields(resource_form_data);
  cy.get('button[name=save]').contains('Valmis').click();
  cy.url().should('include', `/data/fi/dataset/${dataset_name.replace(" ", "-")}`);
})

// Edits an existing dataset
Cypress.Commands.add('edit_dataset', (dataset_name, dataset_form_data) => {

  if (!dataset_form_data) {
    dataset_form_data = {
      "#field-title_translated-fi": 'edit',
    }
  }
  cy.get(`a[href='/data/fi/dataset/edit/${dataset_name}']`).click();
  cy.fill_form_fields(dataset_form_data)
  cy.get('button[name=save]').click();
  cy.get('.dataset-title').contains(dataset_name+'edit');
})

// Deletes a dataset and verifies that it is not found in the search anymore
Cypress.Commands.add('delete_dataset', (dataset_name) => {
  cy.get(`a[href='/data/fi/dataset/edit/${dataset_name}']`).click();
  cy.get('.form-actions').contains('Poista').click();
  cy.contains('Haluatko varmasti poistaa tietoaineiston');
  cy.get('body').find('.btn').contains('Vahvista').click();
  cy.get('.search-input .search').type(dataset_name + '{enter}');
  cy.get(`a[href="/data/fi/dataset/${dataset_name}"]`).should('not.exist');
  cy.visit(`/data/fi/dataset/${dataset_name}`);
  cy.get('.deleted').should('exist');
});


// Creates a new showcase filling both showcase and resource forms
Cypress.Commands.add('create_new_showcase', (showcase_name, showcase_form_data) => {

  // Default values for showcase
  if (!showcase_form_data) {
    showcase_form_data = {
      "#field-title": showcase_name,
      '#field-notes_translated-fi': 'Dataset test description',
      '#s2id_autogen1': 'test_keyword {enter}',
      '#field-author': 'test author'
    }
  }

  // Showcase form
  cy.get('#second-navbar a[href="/data/fi/showcase"]').click();
  cy.get('a[href="/data/fi/showcase/new"]').click();
  cy.get('.slug-preview button').contains('Muokkaa').click();
  cy.get('#field-name').type(showcase_name);
  cy.fill_form_fields(showcase_form_data);
  cy.get('button[name=save]').click();

  // Datasets form
  cy.get(`article a[href="/data/fi/showcase/${showcase_name}"]`).click();
  cy.url().should('include', `/data/fi/showcase/${showcase_name}`);
})

// Creates a new private (hidden) showcase using the publicly available form
// Expects to be at the showcase page in the beginning and returns there when finished
Cypress.Commands.add('create_new_showcase_using_public_form', (showcase_name, showcase_form_data) => {

  // Default values for showcase
  if (!showcase_form_data) {
    showcase_form_data = {
      "#field-title": showcase_name,
      '#field-notes_translated-fi': 'Showcase test description',
      '#notifier': 'test author',
      '#notifier_email': 'test@example.com'
    }
  }

  // Showcase form
  cy.get('a[href="/data/fi/submit-showcase"]').click();
  cy.fill_form_fields(showcase_form_data);
  cy.get('button[name=save]').click();
  cy.get('nav a[href="/data/fi/showcase"]').click();
})

// Edits an existing showcase
Cypress.Commands.add('edit_showcase', (showcase_name, showcase_form_data) => {

  if (!showcase_form_data) {
    showcase_form_data = {
      "#field-title": 'edit',
    }
  }
  cy.get(`a[href='/data/fi/showcase/edit/${showcase_name}']`).first().click();
  cy.fill_form_fields(showcase_form_data)
  cy.get('button[name=save]').click();
  cy.get('.page-heading').contains(showcase_name+'edit');
})

// Deletes a showcase and verifies that it is not found in the search anymore
Cypress.Commands.add('delete_showcase', (showcase_name) => {
  cy.get(`a[href='/data/fi/showcase/edit/${showcase_name}']`).click();
  cy.get('.form-actions').contains('Poista')
    .should('have.attr', 'href')
    .then((href) => {
         cy.visit(href)
    });
  cy.contains('Haluatko varmasti poistaa sovelluksen');
  cy.get('body').find('.btn').contains('Vahvista').click();
  cy.visit('/data/showcase');
  cy.get('.search-input .search').type(showcase_name + '{enter}');
  cy.get('.showcase-list').should('not.exist');
  cy.contains("Sovelluksia ei löytynyt");
})

Cypress.Commands.add('reset_db', () => {
    if (Cypress.env('resetDB') === true){
      cy.exec('npm run reset:db');
      cy.exec("vagrant ssh -c  \'sudo /usr/lib/ckan/default/bin/paster --plugin=ckan search-index clear --config=/etc/ckan/default/test.ini\'", {timeout: 120*1000});
    }
});

Cypress.Commands.add('create_category', function (category_name) {


  cy.visit('/data/group');
  cy.get('a[href="/data/group/new"]').contains("Lisää").click();
  cy.get('.slug-preview button').contains('Muokkaa').click();
  cy.get("input[name='name']").type(category_name);
  cy.get('#field-title_translated-fi').type(category_name);
  cy.get('#field-title_translated-sv').type(category_name);
  cy.get('#field-title_translated-en').type(category_name);

  cy.get('button[name="save"]').click();

});


// for iframe...
Cypress.Commands.add(
  'iframeLoaded',
  { prevSubject: 'element' },
  ($iframe) => {
    const contentWindow = $iframe.prop('contentWindow')
    return new Promise(resolve => {
      if (
        contentWindow &&
        contentWindow.document.readyState === 'complete'
      ) {
        resolve(contentWindow)
      } else {
        $iframe.on('load', () => {
          resolve(contentWindow)
        })
      }
    })
  })

Cypress.Commands.add(
  'getInDocument',
  { prevSubject: 'document' },
  (document, selector) => Cypress.$(selector, document)
)


// generate random end to new data - ei toimi näin täältä - pitää muokata - jos asetettu testitapaukseen toimii
function url_Alpha_Numeric() {
  var text = "";
  var possible = "abcdefghijklmnopqrstuvwxyz0123456789";

  for (var i = 0; i < 10; i++)
    text += possible.charAt(Math.floor(Math.random() * possible.length));

  return text;
}