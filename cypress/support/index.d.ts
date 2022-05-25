/// <reference types="cypress" />

declare namespace Cypress {
  interface Chainable<Subject> {
    login_post_request(username: string, password: string): Chainable<any>
    login(username: string, password: string): Chainable<any>
    logout(): Chainable<any>
    logout_request(): Chainable<any>
    fill_form_fields(form_data: object): Chainable<any>
    create_new_organization(organization_name: string, organization_form_data: object): Chainable<any>
    create_new_dataset(dataset_name: string, dataset_form_data?: object, resource_form_data?: object, parent_organization?: string): Chainable<any>
    edit_dataset(dataset_name: string, dataset_form_data: object): Chainable<any>
    delete_dataset(dataset_name: string): Chainable<any>
    create_new_showcase(showcase_name: string, showcase_form_data?: object): Chainable<any>
    create_new_showcase_using_public_form(showcase_name: string, showcase_form_data: object): Chainable<any>
    edit_showcase(showcase_name: string, showcase_form_data: object): Chainable<any>
    delete_showcase(showcase_name: string): Chainable<any>,
    add_showcase_user(): Chainable<any>,
    reset_db(): Chainable<any>
    create_category(category_name: string): Chainable<any>,
    switch_language(language: string): Chainable<any>
  }
}
