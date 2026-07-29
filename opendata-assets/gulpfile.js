import * as gulp from 'gulp';
import {deleteAsync} from 'del';
import pump from "pump";
import base64 from "gulp-base64-inline";
import concat from "gulp-concat";
import imagemin from "gulp-imagemin";
import imageminJpegoptim from "imagemin-jpegoptim";
import sourcemaps from "gulp-sourcemaps";
import prefixer from "gulp-autoprefixer";
import cleancss from "gulp-clean-css";

import * as dartSass from 'sass';
import gulpSass from 'gulp-sass';
const sass = gulpSass(dartSass);

import template from "gulp-template";
import npmDist from "gulp-npm-dist";
import rename from "gulp-rename";
import gulpStylelint from "@ronilaukkarinen/gulp-stylelint";

const timestamp = new Date().getTime();

const paths = {
  src: {
    vendor: "src/vendor",
    fontawesome: "./node_modules/@fortawesome/fontawesome-pro",
    static_pages: "src/static_pages",
    images: "src/images/**/*",
    scss: "src/scss",
    ckan: "src/scss/ckan",
    drupal: "src/scss/drupal/style.scss",
    drupal_ckeditor_plugins: "src/scss/drupal/custom-elements.scss",
    drupal_ckeditor5_plugins: ["src/scss/drupal/custom-elements.scss", "src/scss/drupal/editor.scss"],
    fonts: "src/fonts/**/*",
    fontsCss: "src/scss/fonts.scss",
    scripts: "src/scripts/**/*",
    drupal_avoindata_header: "../drupal/modules/avoindata-header/src/js/avoindata_header.js",
    bootstrap_styles: "./node_modules/bootstrap/scss/",
    bootstrap_scripts: "./node_modules/bootstrap/js/dist/*",
  },
  drupalTheme: "../drupal/modules/avoindata-theme",
  ckanPublic: "../ckan/ckanext/ckanext-ytp_main/ckanext/ytp/public",
  ckanResources: "../ckan/ckanext/ckanext-ytp_main/ckanext/ytp/resources",
}

export const clean = () => deleteAsync([
  paths.src.vendor,
  paths.ckanResources + '/styles',
  paths.ckanResources + '/scripts',
  paths.ckanResources + '/vendor',
  paths.drupalTheme + '/css',
  paths.drupalTheme + '/fonts',
  paths.drupalTheme + '/vendor',
  paths.drupalTheme + '/static'
],{
    force: true
})


const copyFontawesomeScss = (done) => {
  pump([
    gulp.src(paths.src.fontawesome + "/scss/*.scss"),
    gulp.dest(paths.src.vendor + "/@fortawesome/fontawesome/scss")
  ], done)
};

const staticCss = (done) => {
    pump([
      gulp.src(paths.src.static_pages + "/css/main.css"),
      base64('../../resources/images'),
      concat("error.css"),
      gulp.dest(paths.drupalTheme + "/css")
    ], done)
}


const copyStaticPages = (done) => {
  pump([
    gulp.src(paths.src.static_pages + "/*.html"),
    gulp.dest(paths.drupalTheme + "/static")
  ], done)
}

const images = (done) => {
  pump([
    gulp.src(paths.src.images, {encoding: false}),
    imagemin([
      imagemin.mozjpeg(),
      imagemin.optipng(),
      imageminJpegoptim({
        max: 90
      }),
      imagemin.svgo({
        plugins: [
          {removeViewBox: true},
          {cleanupIDs: false}
        ]
      })
    ]),
    gulp.dest(paths.drupalTheme + "/images"),
    gulp.dest(paths.ckanPublic + "/images")
  ], done)
}

export const staticPages = gulp.series(images, staticCss, copyStaticPages)

const ckan = (done) => {
  pump([
    gulp.src(paths.src.ckan + "/*.scss"),
    sourcemaps.init(),
    sass({ paths: [paths.src.ckan], includePaths: ["node_modules", paths.src.bootstrap_styles] }),
    prefixer(),
    cleancss({ keepBreaks: false }),
    concat("ckan.css"),
    sourcemaps.write("."),
    gulp.dest(paths.ckanResources + "/styles"),
  ], done)
}

const openapiView = (done) => {
  pump([
    gulp.src(paths.src.scss + "/openapi_view.scss"),
    sourcemaps.init(),
    sass({includePaths: ["node_modules", paths.src.bootstrap_styles]}),
    prefixer(),
    cleancss({ keepBreaks: false }),
    concat("openapi_view.css"),
    gulp.dest(paths.ckanResources + "/styles"),
  ], done)
}

// // Compiles scss files in Drupal theme directory
// // Output destination is also in Drupal theme directory
const drupal =  (done) => {
  pump([
    gulp.src(paths.src.drupal),
    sourcemaps.init(),
    sass({ paths: [paths.src.drupal], includePaths: ["node_modules", paths.src.bootstrap_styles]}),
    prefixer(),
    template({ timestamp: timestamp }),
    cleancss({ keepBreaks: false }),
    concat("style.css"),
    sourcemaps.write("./maps"),
    gulp.dest(paths.drupalTheme + "/css"),
  ], done)
}

const drupal_copy_custom_element_styles_to_plugin = (done) => {
  pump([
    gulp.src(paths.src.drupal_ckeditor_plugins),
    sourcemaps.init(),
    sass({ paths: [paths.src.drupal_ckeditor_plugins], includePaths: ["node_modules", paths.src.bootstrap_styles] }),
    prefixer(),
    template({ timestamp: timestamp }),
    cleancss({ keepBreaks: false }),
    concat("style.css"),
    sourcemaps.write("./maps"),
    gulp.dest("../drupal/modules/avoindata-ckeditor-plugins/css"),
  ], done)
}

 const drupal_copy_custom_ckeditor_styles_to_plugin = (done) => {
   pump([
     gulp.src(paths.src.drupal_ckeditor5_plugins),
     sass({paths: paths.src.drupal_ckeditor5_plugins, includePaths: ["node_modules", paths.src.bootstrap_styles]}),
     cleancss({
       format: {
         semicolonAfterLastProperty: true,
         indentBy: 2,
         breaks: {
           afterAtRule: 2,
           afterBlockBegins: 1,
           afterBlockEnds: 2,
           afterComment: 1,
           afterProperty: 1,
           afterRuleBegins: 1,
           afterRuleEnds: 1,
           beforeBlockEnds: 1,
           betweenSelectors: 1
         },
         spaces: {
           aroundSelectorRelation: true, // controls if spaces come around selector relations; e.g. `div > a`; defaults to `false`
           beforeBlockBegins: true, // controls if a space comes before a block begins; e.g. `.block {`; defaults to `false`
           beforeValue: true // controls if a space comes before a value; e.g. `width: 1rem`; defaults to `false`
         }
       }
     }),
     template({timestamp: timestamp}),
     concat("styles.css"),
     gulp.dest("../drupal/modules/avoindata-ckeditor5-plugins/css")
   ], done)
 }

// Copy toolbar styles to avoindata-ckeditor5-plugins
const toolbarIcons = (done) => {
  pump([
    gulp.src('src/toolbar-icons/*.svg'),
    imagemin([
      imagemin.svgo()
    ]),
    gulp.dest("../drupal/modules/avoindata-ckeditor5-plugins/icons"),
  ], done)
}


const toolbarIconStyles = (done) => {
  pump([
    gulp.src('src/toolbar-icons/toolbar-icons.css'),
    base64("/../../src/toolbar-icons/"),
    gulp.dest("../drupal/modules/avoindata-ckeditor5-plugins/css"),
  ], done)
}

const fonts = (done) => {
  pump([
    gulp.src(paths.src.fonts, {encoding: false}),
    gulp.dest(paths.drupalTheme + "/fonts"),
    gulp.dest(paths.ckanResources + "/fonts")
  ], done)
}

// Separate fonts to their own css to optimize their loading
const fontsCss = (done) => {
  pump([
    gulp.src(paths.src.fontsCss),
    sourcemaps.init(),
    sass({ paths: [paths.src.fontsCss] }),
    prefixer(),
    template({ timestamp: timestamp }),
    cleancss({ keepBreaks: false }),
    concat("fonts.css"),
    sourcemaps.write("./maps"),
    gulp.dest(paths.drupalTheme + "/css"),
    gulp.dest(paths.ckanResources + "/styles"),
  ], done)
}

const scripts = (done) => {
  pump([
    gulp.src([paths.src.scripts, paths.src.drupal_avoindata_header]),
    gulp.dest(paths.ckanResources + "/scripts"),
  ], done)
}

const copyVendor = (done) => {
  pump([
    gulp.src(paths.src.vendor + "/**/*", {encoding: false}),
    gulp.dest(paths.drupalTheme + "/vendor"),
    gulp.dest(paths.ckanResources + "/vendor"),
  ], done)
}


const copyLibs = (done) => {
  pump([
    gulp.src(npmDist(), { base: './node_modules', encoding: false}),
    rename((path) => {
      if (path.extname === '.js' || path.extname === '.css') {
        path.basename = path.basename.replace(".min", "");
      }
      if (path.dirname.includes("fontawesome-pro")) {
        path.dirname = path.dirname.replace('fontawesome-pro', 'fontawesome');
      }

    }),
    gulp.dest(paths.src.vendor)
  ], done)
}

const bootstrap_scripts = (done) => {
  pump([
    gulp.src([paths.src.bootstrap_scripts]),
    gulp.dest(paths.src.vendor + "/bootstrap/js")
  ], done)
}

const bootstrap_styles = (done) => {
  pump([
    gulp.src(paths.src.scss + "/bootstrap_build.scss"),
    sass({ includePaths: ["node_modules", paths.src.bootstrap_styles] }),
    concat("bootstrap.css"),
    gulp.dest(paths.src.vendor + "/bootstrap/dist/css"),
    cleancss({ keepBreaks: false }),
    concat("bootstrap.min.css"),
    gulp.dest(paths.src.vendor + "/bootstrap/dist/css"),
  ], done)
}

export const vendor = gulp.series(copyLibs,bootstrap_scripts, bootstrap_styles, copyVendor)


const build = gulp.series(clean, copyFontawesomeScss, gulp.parallel(
  staticPages,
  ckan,
  openapiView,
  drupal,
  drupal_copy_custom_element_styles_to_plugin,
  gulp.parallel(gulp.series(toolbarIcons, toolbarIconStyles), drupal_copy_custom_ckeditor_styles_to_plugin),
  fonts,
  fontsCss,
  scripts,
  vendor
))

export default build;


export const lint = (done) => {
  pump([
    gulp.src(paths.src.scss + '/**/*.scss'),
    gulpStylelint({
      failAfterError: true,
      reporters: [
        {formatter: 'string', console: true}
      ]
    })
  ], done)
}
