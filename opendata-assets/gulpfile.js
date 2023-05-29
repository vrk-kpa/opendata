var fs = require('fs');
var gulp = require("gulp");
var concat = require("gulp-concat");
var imagemin = require("gulp-imagemin");
var sass = require("gulp-sass")(require("sass"));
var sourcemaps = require("gulp-sourcemaps");
var prefixer = require("gulp-autoprefixer");
var del = require("del");
var template = require("gulp-template");
var cleancss = require("gulp-clean-css");
var terser = require("gulp-terser");
var base64 = require("gulp-base64-inline");
var pump = require("pump");
var npmDist = require('gulp-npm-dist');
var rename = require('gulp-rename');
var imageminJpegoptim = require('imagemin-jpegoptim');
var gulpStylelint = require('gulp-stylelint');

var paths = {
  src: {
    images: "src/images/**/*",
    scss: "src/scss",
    ckan: "src/scss/ckan",
    drupal: "src/scss/drupal/style.scss",
    drupal_avoindata_header: "../drupal/modules/avoindata-header/resources/avoindata_header.js",
    drupal_ckeditor_plugins: "src/scss/drupal/custom-elements.scss",
    templates: "src/templates/**/*",
    static_pages: "src/static_pages",
    fonts: "src/fonts/**/*",
    fontsCss: "src/scss/fonts.scss",
    scripts: "src/scripts/**/*",
    bootstrap_styles: "./node_modules/bootstrap-sass/assets/stylesheets",
    bootstrap_scripts: "./node_modules/bootstrap-sass/assets/javascripts/*",
    bootstrap_fonts: "./node_modules/bootstrap-sass/assets/fonts/*",
    moment_path: "./node_modules/moment",
    root: "src",
    fontawesome: "./node_modules/@fortawesome/fontawesome-pro"
  },
  dist: "resources",
  ckanResources: "../ckan/ckanext/ckanext-ytp_main/ckanext/ytp/resources",
  ckanPublic: "../ckan/ckanext/ckanext-ytp_main/ckanext/ytp/public",
  drupalTheme: "../drupal/modules/avoindata-theme"
};

if (!fs.existsSync(paths.src.fontawesome)){
  paths.src.fontawesome = "./node_modules/@fortawesome/fontawesome-free";
}

var timestamp = new Date().getTime();

gulp.task("clean", done => {
  del.sync([
    paths.dist,
    paths.root + '/vendor/**',
    paths.ckanResources + '/styles',
    paths.ckanResources + '/scripts',
    paths.ckanResources + '/templates',
    paths.ckanResources + '/vendor',
    paths.ckanPublic + '/vendor',
    paths.drupalTheme + '/css',
    paths.drupalTheme + '/fonts',
    paths.drupalTheme + '/vendor',
    paths.drupalTheme + '/static'
  ], {
    force: true
  });
  done();
});


gulp.task('copy:fontawesomeScss', (done) => {
  pump([
    gulp.src(paths.src.fontawesome + "/scss/*.scss"),
    gulp.dest(paths.src.root + "/vendor/@fortawesome/fontawesome/scss")
  ], done)
});

gulp.task('copy:fontawesomeFonts', (done) => {
  pump([
    gulp.src(paths.src.fontawesome + "/webfonts/*.*"),
    gulp.dest(paths.drupalTheme + "/fonts")
  ], done)
})

gulp.task('copy:fontawesome', (done) => {
  pump([
    gulp.src(paths.src.fontawesome + "/**/**.*"),
    gulp.dest(paths.ckanPublic + "/vendor/@fortawesome/fontawesome"),
    gulp.dest(paths.drupalTheme + "/vendor/@fortawesome/fontawesome")
  ], done)
})


gulp.task('lint', (done) => {
  pump([
    gulp.src(paths.src.scss + '/**/*.scss'),
    gulpStylelint({
      failAfterError: true,
      reporters:[
        {formatter: 'verbose', console: true}
      ]})
  ], done)
});

gulp.task("ckan",(done) => {
  pump([
    gulp.src(paths.src.ckan + "/*.scss"),
    sourcemaps.init(),
    sass({paths: [paths.src.ckan], includePaths: [paths.src.bootstrap_styles]}),
    prefixer(),
    cleancss({ keepBreaks: false }),
    concat("ckan.css"),
    sourcemaps.write("."),
    gulp.dest(paths.dist + "/styles"),
    gulp.dest(paths.ckanResources + "/styles"),
  ], done)
});

gulp.task("openapi_view",(done) => {
  pump([
    gulp.src(paths.src.scss + "/openapi_view.scss"),
    sourcemaps.init(),
    sass({includePaths: [paths.src.bootstrap_styles]}),
    prefixer(),
    cleancss({ keepBreaks: false }),
    concat("openapi_view.css"),
    gulp.dest(paths.dist + "/styles"),
    gulp.dest(paths.ckanResources + "/styles"),
  ], done)
});



// // Compiles scss files in Drupal theme directory
// // Output destination is also in Drupal theme directory
gulp.task("drupal", (done) => {
  pump([
    gulp.src(paths.src.drupal),
    sourcemaps.init(),
    sass({paths: [paths.src.drupal], includePaths: [paths.src.bootstrap_styles]}),
    prefixer(),
    template({ timestamp: timestamp }),
    cleancss({ keepBreaks: false }),
    concat("style.css"),
    sourcemaps.write("./maps"),
    gulp.dest(paths.drupalTheme + "/css"),
  ], done)
});

// // Compiles scss files in Drupal theme directory
// // Output destination is also in Drupal theme directory
gulp.task("drupal_copy_custom_element_styles_to_plugin", (done) => {
  pump([
    gulp.src(paths.src.drupal_ckeditor_plugins),
    sourcemaps.init(),
    sass({paths: [paths.src.drupal_ckeditor_plugins], includePaths: [paths.src.bootstrap_styles]}),
    prefixer(),
    template({ timestamp: timestamp }),
    cleancss({ keepBreaks: false }),
    concat("style.css"),
    sourcemaps.write("./maps"),
    gulp.dest("../drupal/modules/avoindata-ckeditor-plugins/css"),
  ], done)
});

// Separate fonts to their own css to optimize their loading
gulp.task("fontsCss", (done) => {
  pump([
    gulp.src(paths.src.fontsCss),
    sourcemaps.init(),
    sass({paths: [paths.src.fontsCss]}),
    prefixer(),
    template({ timestamp: timestamp }),
    cleancss({ keepBreaks: false }),
    concat("fonts.css"),
    sourcemaps.write("./maps"),
    gulp.dest(paths.drupalTheme + "/css"),
    gulp.dest(paths.ckanPublic + "/vendor/styles"),
  ], done)
});

gulp.task("images", (done) => {
  pump([
    gulp.src(paths.src.images),
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
});

gulp.task("templates", (done) => {
  pump([
    gulp.src(paths.src.templates),
    template({ timestamp: timestamp }),
    gulp.dest(paths.dist + "/templates"),
    gulp.dest(paths.ckanResources + "/templates"),
  ], done)
});

gulp.task("static_css",
  gulp.series('images', (done) => {
  pump([
    gulp.src(paths.src.static_pages + "/css/main.css"),
    base64('../../resources/images'),
    concat("error.css"),
    gulp.dest(paths.drupalTheme + "/css")
  ], done)
}));

gulp.task(
  "static_pages",
  gulp.series("static_css", (done) => {
    pump([
      gulp.src(paths.src.static_pages + "/*.html"),
      gulp.dest(paths.drupalTheme + "/static")
    ], done)
  })
);

gulp.task("fonts", (done) => {
  pump([
    gulp.src(paths.src.fonts),
    gulp.dest(paths.drupalTheme + "/fonts"),
    gulp.dest(paths.ckanPublic + "/vendor/fonts")
  ], done)
});

gulp.task("scripts", (done) => {
  pump([
    gulp.src([paths.src.scripts, paths.src.drupal_avoindata_header]),
    gulp.dest(paths.dist + "/scripts"),
    gulp.dest(paths.ckanResources + "/scripts")
  ], done)
});

gulp.task("bootstrap_scripts", (done) => {
  pump([
    gulp.src([paths.src.bootstrap_scripts]),
    gulp.dest(paths.dist + "/vendor/bootstrap/js")
  ], done)
});

gulp.task("bootstrap_styles", (done) => {
  pump([
    gulp.src(paths.src.bootstrap_styles + "/_bootstrap.scss"),
    sass({paths: [paths.src.bootstrap_styles]}),
    concat("bootstrap.css"),
    gulp.dest(paths.dist + "/vendor"),
    cleancss({ keepBreaks: false }),
    concat("bootstrap.min.css"),
    gulp.dest(paths.dist + "/vendor")
  ], done)
});

gulp.task("bootstrap_fonts", (done) => {
  pump([
    gulp.src(paths.src.bootstrap_fonts),
    gulp.dest(paths.drupalTheme + '/fonts')
  ], done)
})

gulp.task('copy:libs', (done) => {
  pump([
    gulp.src(npmDist({
      excludes: ['/@fortawesome/**/*']
    }), {base: './node_modules'}),
    rename((path) => {
      if (path.extname === '.js' || path.extname === '.css'){
        path.basename = path.basename.replace(".min", "");
      }
    }),
    gulp.dest(paths.src.root + '/vendor')
  ], done)
});

gulp.task("copy:moment", (done) => {
  pump([
    gulp.src(paths.src.moment_path + "/min/**/*"),
    gulp.dest(paths.src.moment_path + "/dist/min")
  ], done)
})

gulp.task("vendor",
  gulp.series(
    "copy:moment",
    "copy:libs",
    "bootstrap_scripts",
    "bootstrap_styles",
    "bootstrap_fonts", (done) => {
    pump([
      gulp.src(paths.src.root + "/vendor/**/*"),
      gulp.dest(paths.drupalTheme + "/vendor"),
      gulp.dest(paths.ckanResources + "/vendor"),
    ], done)
  })
);

gulp.task(
  "minify-vendor-javascript",
  gulp.series("vendor", (done) => {
    pump([
      gulp.src(paths.dist + "/vendor/**/*.js"),
      terser(),
      gulp.dest(paths.dist + "/vendor")
    ], done)
  })
);

gulp.task("config", (done) => {
  pump([
    gulp.src(paths.src.root + "/resource.config"),
    gulp.dest(paths.dist)
  ], done)
});

gulp.task(
  "default",
  gulp.series(
    "clean",
    "config",
    "copy:fontawesomeScss",
    "copy:fontawesomeFonts",
    "copy:fontawesome",
    gulp.parallel(
      "minify-vendor-javascript",
      "templates",
      "static_pages",
      "ckan",
      "openapi_view",
      "drupal",
      "drupal_copy_custom_element_styles_to_plugin",
      "fonts",
      "fontsCss",
      "scripts")
  )
);

gulp.task("watch", () => {
  var watcher = gulp.watch(
    ["./src/scss/**/*.scss", "./src/scss/*.scss", paths.src.templates],
    gulp.series("default")
  );

  watcher.on("change", event => {
    console.log(
      "File " + event.path + " was " + event.type + ", running tasks..."
    );
  });
});

gulp.task("watch_styles", () => {
  var watcher = gulp.watch(
    ["./src/scss/**/*.scss", "./src/scss/*.scss", paths.src.templates],
    gulp.parallel(
      "bootstrap_styles",
      "bootstrap_scripts",
      "vendor",
      "static_pages",
      "ckan",
      "drupal",
      "drupal_copy_custom_element_styles_to_plugin",
      "fontsCss",
      "lint"
    )
  );

  watcher.on("change", event => {
    console.log(
      "File " + event.path + " was " + event.type + ", running tasks..."
    );
  });
});

gulp.task("watch_drupal_styles", () => {
  var watcher = gulp.watch(
    ["src/scss/**/*.scss", "src/scss/*.scss", "../avoindata-theme/scss"],
    gulp.series(
      "drupal",
      "drupal_copy_custom_element_styles_to_plugin",
      "fontsCss",
      "lint"
    )
  );

  watcher.on("change", event => {
    console.log(
      "File " + event.path + " was " + event.type + ", running tasks..."
    );
  });
});
