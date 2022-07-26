/**
 * @file
 */

global.toggleLanguageDropdown = function () {
  document.getElementsByClassName('dropdown-button')[0].classList.toggle("dropdown-open");
  document.getElementsByClassName('dropdown-content')[0].classList.toggle("dropdown-open");
};
