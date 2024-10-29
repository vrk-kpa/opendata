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


//registers an user to the point where the confirm registration email is sent
Cypress.Commands.add('register', (username, email) => {
  cy.visit('/user/register');
  cy.get('#edit-mail').type(email);
  cy.get('#edit-name').type(username);
  cy.get('#edit-submit').click();
});

// MailHog commands
const mhApiUrl = (path) => {
  return `http://localhost:8025/api${path}`;
};

Cypress.Commands.add('mhGetAllMails', () => {
  return cy
    .request({
      method: 'GET',
      url: mhApiUrl('/v2/messages?limit=9999'),
      auth: {'user': 'test', 'password': 'test'}
    })
    .then((response) => {
        if (typeof response.body === 'string') {
            return JSON.parse(response.body);
        } else {
            return response.body;
        }
    })
    .then((parsed) => parsed.items);
});

Cypress.Commands.add('mhFirst', {prevSubject: true}, (mails) => {
  return Array.isArray(mails) && mails.length > 0 ? mails[0] : mails;
});

Cypress.Commands.add('mhGetBody', {prevSubject: true}, (mail) => {
  return cy.wrap(mail.Content).its('Body');
});


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
});

Cypress.Commands.add('logout_request', (username, password) => {
  cy.request({
    method: 'GET',
    url: '/user/logout'
  });
});

Cypress.Commands.add('login', (username, password) => {
  cy.visit('/user/login');
  cy.get('input[name=name]').type(username);
  cy.get('input[name=pass]').type(password);
  cy.get('#edit-submit').click();
  cy.url().should('include', '/data/fi/user');

  cy.getCookies().should('have.length.greaterThan', 0).then((cookies) => {
    let drupal_cookie = cookies.find(cookie => cookie.name.match(/^SESS/))
    expect(drupal_cookie).to.be.an('object').that.have.property('name')
  })
});

Cypress.Commands.add('logout', () => {
  cy.visit('/user/logout');

  // Handle confirmation dialog if it pops up
  if(window.location.pathname.endsWith("/user/logout/confirm")) {
    cy.get('#edit-submit').click();
  }

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
                    // note. Some fields do not appear with the correct value in the cypress UI, but the correct value is still selected 
                    field.select(field_value.value, options)
                    break;
                // TODO: This should not be necessary, but the delay required between typing 
                // and pressing enter is needed because the select2 component won't accept pressing enter
                // immediately after typing in ajax-populated instances
                case 'select2':
                    field_value.values.forEach((v) => {
                      field.type(v, options);
                      // wait for the results load before pressing enter
                      cy.get(`${field_selector}.select2-active`, {timeout: 20000}).should('not.exist');
                      cy.get(field_selector).type('{enter}', {'force': true})
                    })
                    break;
                case 'check':
                    field.check(options)
                    break;
                case 'radio':
                    field.check(field_value.value, options)
                    break;
                case 'datepicker':
                    field.clear();
                    field.type(field_value.value);
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

Cypress.Commands.add('create_organization_for_user', (organization_name, user_name, makeUnique) => {

    if(makeUnique) {
      const uuid = () => Cypress._.random(0, 1e6)
      organization_name = `${organization_name}_${uuid()}`
    }
    cy.login_post_request(user_name, user_name)
    cy.create_new_organization(organization_name);
    cy.logout_request();

    cy.login_post_request('admin', 'administrator');
    cy.approve_organization(organization_name);
    cy.logout_request();
});

Cypress.Commands.add('create_new_dataset', (dataset_name, dataset_form_data, resource_form_data, parent_organization) => {

  // Default values for dataset and resource forms
  if (!dataset_form_data) {
    dataset_form_data = {
      "#field-title_translated-fi": dataset_name,
      '#field-notes_translated-fi': 'Dataset test description',
      // FIXME: This should just be 'test_keyword{enter}', see fill_form_fields in support/commands.js
      '#s2id_autogen1': {type: 'select2', values: ['test_keyword']},
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

  cy.get('button[name=save]').click();

  //Resource form, filled with just the name
  cy.contains('a', 'Linkki').click()
  cy.fill_form_fields(resource_form_data);
  cy.get('button[name=save].suomifi-button-primary').click();
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
});


// Creates a new showcase filling both showcase and resource forms
Cypress.Commands.add('create_new_showcase', (showcase_name, showcase_form_data) => {

  // Default values for showcase
  if (!showcase_form_data) {
    showcase_form_data = {
      "#field-title_translated-fi": showcase_name,
      '#field-notes_translated-fi': 'Dataset test description',
      // FIXME: This should just be 'test_keyword{enter}', see fill_form_fields in support/commands.js
      '#s2id_autogen1': {type: 'select2', values: ['test_keyword']},
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
      '#notifier_email': 'test@example.com',
      '#field-author': 'Author of showcase'
    }
  }

  // Showcase form
  cy.get('a[href="/data/fi/submit-showcase"]').click();
  cy.fill_form_fields(showcase_form_data);
  cy.get('button[name=save]').click();
  cy.get('.alert-success').should('contain', 'Sovelluksen lähetys onnistui')
})

// Edits an existing showcase
Cypress.Commands.add('edit_showcase', (showcase_name, showcase_form_data) => {

  if (!showcase_form_data) {
    showcase_form_data = {
      "#field-title_translated-fi": 'edit',
    }
  }
  cy.get(`a[href='/data/fi/showcase/edit/${showcase_name}']`).first().click();
  cy.fill_form_fields(showcase_form_data)
  cy.get('button[name=save]').click();
  cy.get('.dataset-title').contains(showcase_name+'edit');
})

// Deletes a showcase and verifies that it is not found in the search anymore
Cypress.Commands.add('delete_showcase', (showcase_name) => {
  cy.get(`a[href='/data/fi/showcase/edit/${showcase_name}']`).click();
  cy.get('.form-actions').contains('Poista')
    .should('have.attr', 'href')
    .then((href) => {
      cy.get('button[name=save]').click();
      cy.visit(href);
      cy.contains('Haluatko varmasti poistaa sovelluksen');
      cy.get('body').find('.btn').contains('Vahvista').click();
      cy.visit('/data/showcase');
      cy.get('.search-input .search').type(showcase_name + '{enter}');
    });
});

Cypress.Commands.add('add_showcase_user', () => {
  // Login with test-publisher and visit ckan to create the user
  cy.login_post_request('test-publisher', 'test-publisher');
  cy.request('/data/fi/dataset');
  cy.logout_request();

  // Set showcase-admin rights for test-publisher
  cy.login_post_request('admin', 'administrator');

  // It's necessary to request dataset page before ckan-admin so that the ckan user is created
  cy.request('/data/fi/dataset');
  cy.visit('/data/ckan-admin');
  cy.get('a[href="/data/ckan-admin/showcase_admins"]').click();
  cy.get('#s2id_username').click();
  cy.get('#s2id_autogen1_search').type('test-publisher', {force: true}).wait(1000).type('{enter}');
  cy.get('button[name=submit]').click();
  cy.logout_request();

  // Login with test-publisher
  cy.login_post_request('test-publisher', 'test-publisher');

  // We're forcing the click since drupal toolbar obscures the link
  // and due to cypress-io/cypress#2302 the auto-scrolling does not work
  cy.get('nav a[href="/data/fi/showcase"]').click({force: true});
});

Cypress.Commands.add('reset_db', () => {
    if (Cypress.env('resetDB') === true){
        cy.exec('npm run reset', {
          env: {
            DB_HOST: '127.0.0.1',
            DB_CKAN: 'ckan',
            DB_CKAN_USER: 'ckan',
            DB_CKAN_PASS: 'ckan_pass'
          }
        });

        //const containerName = Cypress.env('test_container_name') || 'opendata_ckan_1';
        //cy.exec(`docker exec -i ${containerName} sh -c "ckan --config /srv/app/production.ini api action sparql_clear"`);
        //cy.exec(`docker exec -i ${containerName} sh -c "ckan --config /srv/app/production.ini search-index clear"`);
        // Init vocaularies
        //cy.exec(`docker exec -i ${containerName} sh -c "ckan --config /srv/app/production.ini sixodp-showcase create_platform_vocabulary"`);
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


/*
 * Apiset helpers
 */
Cypress.Commands.add('create_new_apiset', (apiset_name, apiset_form_data, api_form_data, parent_organization) => {

  // Default values for apiset and resource forms
  if (!apiset_form_data) {
    apiset_form_data = {
      "#field-title_translated-fi": apiset_name,
      '#field-notes_translated-fi': 'Apiset test description',
      // FIXME: This should just be 'test_keyword{enter}', see fill_form_fields in support/commands.js
      '#s2id_autogen1': {type: 'select2', values: ['test_keyword']},
      '#field-api_provider': 'Api Provider',
      '#field-api_provider_email': 'test.maintainer@example.com'
    }
  }
  if (!api_form_data) {
    api_form_data = {
      "#field-name_translated-fi": 'test data',
      '#field-image-url': 'http://example.com'
    }
  }

  // As there isn't currently link for apisets in nav, we must use exact urls on navigation
  cy.visit('/data/fi/apiset/new');
  cy.get('.slug-preview button').contains('Muokkaa').click();
  cy.get('#field-name').type(apiset_name);
  cy.fill_form_fields(apiset_form_data);

  // The selector field is hidden so force is required.
  // The visible UI element for selecting the organization is not as easy to use with cypress
  if (parent_organization) {
    cy.get("#field-organizations").select(parent_organization, {force: true});
  }

  cy.get('button[name=save]').click();

  //Resource form, filled with just the name and api link
  cy.contains('a', 'Linkki').click()
  cy.fill_form_fields(api_form_data);
  cy.get('button[name=save].suomifi-button-primary').click();
  cy.location('pathname', {timeout: 60000}).should('not.contain', `/apiset/${apiset_name}/resource/new`)
  cy.url().should('include', `/data/fi/apiset/${apiset_name}`);
});

// Edits an existing apiset
Cypress.Commands.add('edit_apiset', (apiset_name, apiset_form_data) => {

  if (!apiset_form_data) {
    apiset_form_data = {
      "#field-title_translated-fi": 'edit',
    }
  }
  // As there isn't currently link for apisets in nav, we must use exact urls on navigation
  cy.visit(`/data/fi/apiset/edit/${apiset_name}`);
  cy.fill_form_fields(apiset_form_data)
  cy.get('button[name=save]').click();
  // Check if the url has changed in order to determine when the form has been properly submitted
  cy.url().should('include', `/data/fi/apiset/${apiset_name}`); 
  cy.get('.dataset-title').contains(apiset_name+'edit');
})

// Deletes a dataset and verifies that it is not found in the search anymore
Cypress.Commands.add('delete_apiset', (apiset_name) => {
  // As there isn't currently link for apisets in nav, we must use exact urls on navigation
  cy.visit(`/data/fi/apiset/edit/${apiset_name}`);
  cy.get('.form-actions').contains('Poista').click();
  cy.contains('Haluatko varmasti poistaa rajapinnan');
  cy.get('body').find('.btn').contains('Vahvista').click();
  cy.get('.search-input .search').type(apiset_name + '{enter}');
  cy.get(`a[href="/data/fi/apiset/${apiset_name}"]`).should('not.exist');
  cy.visit(`/data/fi/apiset/${apiset_name}`);
});

Cypress.Commands.add('switch_language', (language) => {
  cy.get('#block-avoindata-language-switcher button').click();
  cy.get('.language-link[hreflang=' + language + ']').click();
})
