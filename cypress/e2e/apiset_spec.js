
describe('Apiset filtering', function(){

  const apiset1_name = 'test_apiset_one';
  const apiset2_name = 'test_apiset_two';
  const apiset1_form_data = {
    '#field-title_translated-fi': apiset1_name,
    '#field-notes_translated-fi': 'test kuvaus',
    '#s2id_autogen1': {type: 'select2', values: ['keyword one']},
    '#field-license_id':{type: 'select', value: 'cc-nc'},
    '#field-api_provider': 'Api Provider',
    '#field-api_provider_email': 'test.provider@example.com',
  }

  const apiset2_form_data = {
    '#field-title_translated-fi': apiset2_name,
    '#field-notes_translated-fi': 'test kuvaus',
    '#s2id_autogen1': {type: 'select2', values: ['keyword two']},
    '#field-license_id':{type: 'select', value: 'cc-by'},
    '#field-api_provider': 'Api Provider',
    '#field-api_provider_email': 'test.provider@example.com',
  }


  const api1_form_data = {
    '#field-name_translated-fi': 'test api',
    '#field-description_translated-fi': 'test kuvaus',
    '#s2id_autogen1_search': {type: 'select2', values: ['CSV'], force:true},
  }

  const api2_form_data = {
    '#field-name_translated-fi': 'test api',
    '#field-description_translated-fi': 'test kuvaus',
    '#s2id_autogen1_search': {type: 'select2', values: ['CSV'], force:true},
  }

  beforeEach(function () {
    cy.visit('/');
    cy.login_post_request('test-user', 'test-user')
    cy.visit("/data/fi/apiset/")
  });

  before(function(){
    cy.reset_db();
    cy.create_organization_for_user('apiset_test_organization', 'test-user', true);

    //create 2 apisets with different filter options
    cy.login_post_request('test-user', 'test-user')
    
    //apiset one
    cy.visit('/data/fi/apiset/new');
    cy.get('.slug-preview button').contains('Muokkaa').click();
    cy.get('#field-name').type(apiset1_name);
    cy.fill_form_fields(apiset1_form_data);
    cy.get('button[name=save]').click();
    cy.fill_form_fields(api1_form_data);
    cy.get('#field-image-upload').selectFile("cypress/sample_text_file.txt")
    cy.get('button[name=save].suomifi-button-primary').click();
    //wait for file to upload properly and the page to render before continuing
    cy.location('pathname', {timeout: 20000}).should('contain', `/dataset/${apiset1_name}`)

    //apiset two
    cy.visit('/data/fi/apiset/new');
    cy.get('.slug-preview button').contains('Muokkaa').click();
    cy.get('#field-name').type(apiset2_name);
    cy.fill_form_fields(apiset2_form_data);
    cy.get('button[name=save]').click();
    cy.fill_form_fields(api2_form_data);
    cy.get('#field-image-upload').selectFile("cypress/FL_insurance_sample.csv")
    cy.get('button[name=save].suomifi-button-primary').click();
  })

  it('Keyword filters are working', function(){
    //keywords and results exist
    cy.get('.secondary > :nth-child(2)').should('contain.text', 'keyword one');
    cy.get('.secondary > :nth-child(2)').should('contain.text', 'keyword two');
    cy.get('.container-search-result').should('contain.text', apiset1_name)
    cy.get('.container-search-result').should('contain.text', apiset2_name)

    //click keyword one filter
    cy.get(':nth-child(2) > nav > .list-unstyled > :nth-child(1) > a > span').click();

    //filter list and results should now only contain the chosen keyword
    cy.get('.secondary > :nth-child(2)').should('contain.text', 'keyword one');
    cy.get('.secondary > :nth-child(2)').should('not.contain.text', 'keyword two');
    cy.get('.container-search-result').should('contain.text', apiset1_name)
    cy.get('.container-search-result').should('not.contain.text', apiset2_name)

    //release the filter
    cy.get('.remove > .fal').click();

    //both keywords and results exist
    cy.get('.secondary > :nth-child(2)').should('contain.text', 'keyword one');
    cy.get('.secondary > :nth-child(2)').should('contain.text', 'keyword two');
    cy.get('.container-search-result').should('contain.text', apiset1_name)
    cy.get('.container-search-result').should('contain.text', apiset2_name)

    //click keyword two filter
    cy.get(':nth-child(2) > nav > .list-unstyled > :nth-child(2) > a > span').click();

    //filter list and results should now only contain the chosen keyword
    cy.get('.secondary > :nth-child(2)').should('not.contain.text', 'keyword one');
    cy.get('.secondary > :nth-child(2)').should('contain.text', 'keyword two');
    cy.get('.container-search-result').should('not.contain.text', apiset1_name);
    cy.get('.container-search-result').should('contain.text', apiset2_name);

    //release the filter
    cy.get('.remove > .fal').click();

    //both keywords and results exist
    cy.get('.secondary > :nth-child(2)').should('contain.text', 'keyword one');
    cy.get('.secondary > :nth-child(2)').should('contain.text', 'keyword two');
    cy.get('.container-search-result').should('contain.text', apiset1_name);
    cy.get('.container-search-result').should('contain.text', apiset2_name);
  })

  it('Organization filters are working', function(){
    //both apisets belong to the same organization, so filter should not affect their visibility
    cy.get('.secondary > :nth-child(3)').should('contain.text', 'apiset_test_organization');
    cy.get('.container-search-result').should('contain.text', apiset1_name);
    cy.get('.container-search-result').should('contain.text', apiset2_name);

    cy.get(':nth-child(3) > nav > .list-unstyled > .nav-item > a > span').click();

    //the results should still be the same
    cy.get('.secondary > :nth-child(3)').should('contain.text', 'apiset_test_organization');
    cy.get('.container-search-result').should('contain.text', apiset1_name);
    cy.get('.container-search-result').should('contain.text', apiset2_name);

    //release the filter
    cy.get('.remove > .fal').click();

    //the results should still be the same
    cy.get('.secondary > :nth-child(3)').should('contain.text', 'apiset_test_organization');
    cy.get('.container-search-result').should('contain.text', apiset1_name);
    cy.get('.container-search-result').should('contain.text', apiset2_name);

  });

  it('Fileformat filters are working', function(){
    cy.get('.secondary > :nth-child(4)').should('contain.text', 'csv');
    cy.get('.secondary > :nth-child(4)').should('contain.text', 'txt');
    cy.get('.container-search-result').should('contain.text', apiset1_name);
    cy.get('.container-search-result').should('contain.text', apiset2_name);

    //filter to csv
    cy.get(':nth-child(4) > nav > .list-unstyled > :nth-child(1) > a > span').click();

    //should not contain apiset1 (txt)
    cy.get('.secondary > :nth-child(4)').should('contain.text', 'csv');
    cy.get('.secondary > :nth-child(4)').should('not.contain.text', 'txt');
    cy.get('.container-search-result').should('not.contain.text', apiset1_name);
    cy.get('.container-search-result').should('contain.text', apiset2_name);

    //release the filter
    cy.get('.remove > .fal').click();

    cy.get('.secondary > :nth-child(4)').should('contain.text', 'csv');
    cy.get('.secondary > :nth-child(4)').should('contain.text', 'txt');
    cy.get('.container-search-result').should('contain.text', apiset1_name);
    cy.get('.container-search-result').should('contain.text', apiset2_name);

    //filter to txt
    cy.get(':nth-child(4) > nav > .list-unstyled > :nth-child(2) > a > span').click();

    //should not contain apiset2 (csv)
    cy.get('.secondary > :nth-child(4)').should('not.contain.text', 'csv');
    cy.get('.secondary > :nth-child(4)').should('contain.text', 'txt');
    cy.get('.container-search-result').should('contain.text', apiset1_name);
    cy.get('.container-search-result').should('not.contain.text', apiset2_name);

    //release the filter
    cy.get('.remove > .fal').click();

    cy.get('.secondary > :nth-child(4)').should('contain.text', 'csv');
    cy.get('.secondary > :nth-child(4)').should('contain.text', 'txt');
    cy.get('.container-search-result').should('contain.text', apiset1_name);
    cy.get('.container-search-result').should('contain.text', apiset2_name);
  });

  it('Licence filters are working', function(){
    cy.get('.secondary > :nth-child(5)').should('contain.text', 'Creative Commons Attribution');
    cy.get('.secondary > :nth-child(5)').should('contain.text', 'Creative Commons Non-Commercial');
    cy.get('.container-search-result').should('contain.text', apiset1_name);
    cy.get('.container-search-result').should('contain.text', apiset2_name);

    //filter by Creative Commons Attribution
    cy.get(':nth-child(5) > nav > .list-unstyled > :nth-child(1) > a > span').click();

    cy.get('.secondary > :nth-child(5)').should('contain.text', 'Creative Commons Attribution');
    cy.get('.secondary > :nth-child(5)').should('not.contain.text', 'Creative Commons Non-Commercial');
    cy.get('.container-search-result').should('not.contain.text', apiset1_name);
    cy.get('.container-search-result').should('contain.text', apiset2_name);

    //release the filter
    cy.get('.remove > .fal').click();

    cy.get('.secondary > :nth-child(5)').should('contain.text', 'Creative Commons Attribution');
    cy.get('.secondary > :nth-child(5)').should('contain.text', 'Creative Commons Non-Commercial');
    cy.get('.container-search-result').should('contain.text', apiset1_name);
    cy.get('.container-search-result').should('contain.text', apiset2_name);
   
    //filter by Creative Commons Non-Commercial
    cy.get(':nth-child(5) > nav > .list-unstyled > :nth-child(2) > a > span').click();

    cy.get('.secondary > :nth-child(5)').should('not.contain.text', 'Creative Commons Attribution');
    cy.get('.secondary > :nth-child(5)').should('contain.text', 'Creative Commons Non-Commercial');
    cy.get('.container-search-result').should('contain.text', apiset1_name);
    cy.get('.container-search-result').should('not.contain.text', apiset2_name);

    //release the filter
    cy.get('.remove > .fal').click();

    cy.get('.secondary > :nth-child(5)').should('contain.text', 'Creative Commons Attribution');
    cy.get('.secondary > :nth-child(5)').should('contain.text', 'Creative Commons Non-Commercial');
    cy.get('.container-search-result').should('contain.text', apiset1_name);
    cy.get('.container-search-result').should('contain.text', apiset2_name);
  })
})

describe('Apiset tests', function() {

  beforeEach(function () {
    cy.login_post_request('test-user', 'test-user')
    cy.visit('/');
  });

  before(function(){
    cy.reset_db();
    cy.create_organization_for_user('apiset_test_organization', 'test-user', true);
  })

  it('Create a new minimal api, edit it and delete it', function() {
    const apis_name = 'test_api';
    cy.create_new_apiset(apis_name);
    cy.edit_apiset(apis_name);

    // Delete and make sure it was deleted. Edit doesn't affect the apiset name in url, so the unmodified
    // name is passed as a parameter
    cy.delete_apiset(apis_name);
  });

  it("Create minimal apiset and add file as a api", function(){
    const apiset = 'test_apiset_with_file';

    const apiset_form_data = {
      "#field-title_translated-fi": apiset,
      '#field-notes_translated-fi': 'Apiset test description',
      // FIXME: This should just be 'test_keyword{enter}', see fill_form_fields in support/commands.js
      '#s2id_autogen1': {type: 'select2', values: ['test_keyword']},
      '#field-api_provider': 'Api Provider',
      '#field-api_provider_email': 'test.provider@example.com'
    };

    cy.visit('/data/fi/apiset/new');
    cy.get('.slug-preview button').contains('Muokkaa').click();
    cy.get('#field-name').type(apiset);
    cy.fill_form_fields(apiset_form_data);
    cy.get('button[name=save]').click();


    const api = 'sample file';
    const api_form_data = {
      "#field-name_translated-fi": api
    };
    cy.fill_form_fields(api_form_data);

    cy.get('#field-image-upload').selectFile("cypress/FL_insurance_sample.csv")

    cy.get('button[name=save].suomifi-button-primary').click();

    // if cloudstorage is enabled, we wait for window.location to change
    if (Cypress.env('cloudStorageEnabled')){
      cy.location('pathname', {timeout: 20000}).should('not.include', '/resource/new');
    }

    cy.get('a').contains(api).click();

    cy.get('a').contains('Lataa')
      .should('have.attr', 'href')
      .then(function (href) {
        cy.request(href).its('status')
          .should('eq', 200)
    });
  });

  it('Create an apiset with all fields', function() {
    const apiset_name = 'test_apiset_with_all_fields';
    const apiset_form_data = {
      '#field-title_translated-fi': apiset_name,
      '#field-title_translated-en': apiset_name,
      '#field-title_translated-sv': apiset_name,
      '#field-notes_translated-fi': 'test kuvaus',
      '#field-notes_translated-en': 'test description',
      '#field-notes_translated-sv': 'test beskrivning',
      // FIXME: These should just be 'value{enter}' for each, see fill_form_fields in support/commands.js
      '#s2id_autogen1': {type: 'select2', values: ['test']},
      '#s2id_autogen2': {type: 'select2', values: ['test']},
      '#s2id_autogen3': {type: 'select2', values: ['test']},
      '#field-private': 'False',
      '#field-license_id': 'cc-by-4.0',
      '#field-access_rights-fi': 'Käyttöoikeudet',
      '#field-access_rights-en': 'Käyttöoikeudet',
      '#field-access_rights-sv': 'Käyttöoikeudet',
      '#field-api_provider': 'Api Provider',
      '#field-api_provider_email': 'test.provider@example.com',
    };

    const api_form_data = {
      '#field-name_translated-fi': 'test api',
      '#field-name_translated-en': 'test api',
      '#field-name_translated-sv': 'test api',
      '#field-image-url': 'http://example.com',
      '#field-description_translated-fi': 'test kuvaus',
      '#field-description_translated-en': 'test description',
      '#field-description_translated-sv': 'test beskrivning',
      '#field-documentation_translated-fi': 'test dokumentaatio',
      '#field-documentation_translated-en': 'test dokumentaatio',
      '#field-documentation_translated-sv': 'test dokumentaatio',
      '[name="registration_required"]': {type: 'radio', value: 'true', force: true},
      // FIXME: These should just be 'value{enter}' for each, see fill_form_fields in support/commands.js
      '#s2id_autogen1_search': {type: 'select2', values: ['CSV'], force:true},
    };
    cy.create_new_apiset(apiset_name, apiset_form_data, api_form_data);
  });

  it('Creating an empty apiset fails', function() {
    cy.visit('/data/fi/apiset/new');
    cy.get('button[name=save]').click();
    cy.get('.error-explanation');
    cy.visit('/');
  });

  it('Cannot create apiset if logged out', function() {
    cy.logout_request();
    cy.visit(('/data/fi/apiset/new'), {
      failOnStatusCode: false
    });
    cy.contains('Ei oikeuksia luoda tietoaineistoa');
  });
})
