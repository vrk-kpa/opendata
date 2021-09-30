var fs = require('fs');
var gulp = require("gulp");
var concat = require("gulp-concat");
var imagemin = require("gulp-imagemin");
var less = require("gulp-less");
var sourcemaps = require("gulp-sourcemaps");
var prefixer = require("gulp-autoprefixer");
var del = require("del");
var template = require("gulp-template");
var inlineCss = require("gulp-inline-css");
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
    less: "src/less",
    ckan: "src/less/ckan",
    drupal: "src/less/drupal/style.less",
    drupal_avoindata_header: "../avoindata-drupal-header/resources/avoindata_header.js",
    drupal_ckeditor_plugins: "src/less/drupal/custom-elements.less",
    templates: "src/templates/**/*",
    static_pages: "src/static_pages",
    font: "src/font/**/*",
    fonts: "src/fonts/**/*",
    fontsCss: "src/less/fonts.less",
    scripts: "src/scripts/**/*",
    bootstrap_styles: "node_modules/bootstrap/less",
    bootstrap_scripts: "node_modules/bootstrap/js/*",
    moment_path: "node_modules/moment",
    root: "src"
  },
  dist: "resources"
};

let fontawesomeLessPath = 'node_modules/@fortawesome/fontawesome-pro/less';
if (!fs.existsSync('node_modules/@fortawesome/fontawesome-pro')){
  fontawesomeLessPath = 'node_modules/@fortawesome/fontawesome-free/less'
}

var timestamp = new Date().getTime();

gulp.task("clean", done => {
  del.sync([paths.dist, paths.root + '/vendor/**']);
  done();
});


gulp.task('copy:fontawesomeLess', (done) => {
  pump([
    gulp.src(fontawesomeLessPath + "/*.less"),
    gulp.dest(paths.src.root + "/vendor/@fortawesome/fontawesome/less")
  ], done)
});


gulp.task('lint', (done) => {
  pump([
    gulp.src(paths.src.less + '/**/*.less'),
    gulpStylelint({
      failAfterError: true,
      reporters:[
        {formatter: 'verbose', console: true}
      ]})
  ], done)
});

gulp.task("ckan",(done) => {
  pump([
    gulp.src(paths.src.ckan + "/*.less"),
    sourcemaps.init(),
    less({paths: [paths.src.ckan]}),
    prefixer(),
    cleancss({ keepBreaks: false }),
    concat("ckan.css"),
    sourcemaps.write("."),
    gulp.dest(paths.dist + "/styles")
  ], done)
});

gulp.task("openapi_view",(done) => {
  pump([
    gulp.src(paths.src.less + "/openapi_view.less"),
    sourcemaps.init(),
    less(),
    prefixer(),
    cleancss({ keepBreaks: false }),
    concat("openapi_view.css"),
    gulp.dest(paths.dist + "/styles")
  ], done)
});



// // Compiles Less files in Drupal theme directory
// // Output destination is also in Drupal theme directory
gulp.task("drupal", (done) => {
  pump([
    gulp.src(paths.src.drupal),
    sourcemaps.init(),
    less({paths: [paths.src.drupal]}),
    prefixer(),
    template({ timestamp: timestamp }),
    cleancss({ keepBreaks: false }),
    concat("style.css"),
    sourcemaps.write("./maps"),
    gulp.dest("../avoindata-drupal-theme/css"),
  ], done)
});

// // Compiles Less files in Drupal theme directory
// // Output destination is also in Drupal theme directory
gulp.task("drupal_copy_custom_element_styles_to_plugin", (done) => {
  pump([
    gulp.src(paths.src.drupal_ckeditor_plugins),
    sourcemaps.init(),
    less({paths: [paths.src.drupal_ckeditor_plugins]}),
    prefixer(),
    template({ timestamp: timestamp }),
    cleancss({ keepBreaks: false }),
    concat("style.css"),
    sourcemaps.write("./maps"),
    gulp.dest("../avoindata-drupal-ckeditor-plugins/css"),
  ], done)
});

// Separate fonts to their own css to optimize their loading
gulp.task("fontsCss", (done) => {
  pump([
    gulp.src(paths.src.fontsCss),
    sourcemaps.init(),
    less({paths: [paths.src.fontsCss]}),
    prefixer(),
    template({ timestamp: timestamp }),
    cleancss({ keepBreaks: false }),
    concat("fonts.css"),
    sourcemaps.write("./maps"),
    gulp.dest(paths.dist + "/styles"),
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
    gulp.dest(paths.dist + "/images")
  ], done)
});

gulp.task("templates", (done) => {
  pump([
    gulp.src(paths.src.templates),
    template({ timestamp: timestamp }),
    gulp.dest(paths.dist + "/templates")
  ], done)
});

gulp.task("static_css",
  gulp.series('images', (done) => {
  pump([
    gulp.src(paths.src.static_pages + "/css/main.css"),
    base64('../../resources/images'),
    concat("style.css"),
    gulp.dest(paths.src.static_pages + "/css")
  ], done)
}));

gulp.task(
  "static_pages",
  gulp.series("static_css", (done) => {
    pump([
      gulp.src(paths.src.static_pages + "/*.html"),
      inlineCss(),
      gulp.dest(paths.dist + "/static")
    ], done)
  })
);

gulp.task("fonts", (done) => {
  pump([
    gulp.src(paths.src.fonts),
    gulp.dest(paths.dist + "/fonts")
  ], done)
});

gulp.task("font", (done) => {
  pump([
    gulp.src(paths.src.font),
    gulp.dest(paths.dist + "/font")
  ], done)
});

gulp.task("scripts", (done) => {
  pump([
    gulp.src([paths.src.scripts, paths.src.drupal_avoindata_header]),
    gulp.dest(paths.dist + "/scripts")
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
    gulp.src(paths.src.bootstrap_styles + "/bootstrap.less"),
    less({paths: [paths.src.bootstrap_styles]}),
    concat("bootstrap.css"),
    gulp.dest(paths.dist + "/vendor"),
    cleancss({ keepBreaks: false }),
    concat("bootstrap.min.css"),
    gulp.dest(paths.dist + "/vendor")
  ], done)
});

gulp.task('copy:libs', (done) => {
  pump([
    gulp.src(npmDist({
    }), {base: './node_modules'}),
    rename((path) => {
      if (path.extname === '.js' || path.extname === '.css'){
        path.basename = path.basename.replace(".min", "");
      }
      if (path.dirname.includes("-pro")){
        path.dirname = path.dirname.replace("-pro", "");
      }
      if (path.dirname.includes("-free")){
        path.dirname = path.dirname.replace("-free", "");
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
    "copy:libs", (done) => {
    pump([
      gulp.src(paths.src.root + "/vendor/**/*"),
      gulp.dest(paths.dist + "/vendor"),
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
    "copy:fontawesomeLess",
    "lint",
    gulp.parallel(
      "bootstrap_styles",
      "bootstrap_scripts",
      "minify-vendor-javascript",
      "templates",
      "static_pages",
      "ckan",
      "openapi_view",
      "drupal",
      "drupal_copy_custom_element_styles_to_plugin",
      "fonts",
      "font",
      "fontsCss",
      "scripts")
  )
);

gulp.task("watch", () => {
  var watcher = gulp.watch(
    ["./src/less/**/*.less", "./src/less/*.less", paths.src.templates],
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
    ["./src/less/**/*.less", "./src/less/*.less", paths.src.templates],
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
    ["./src/less/**/*.less", "./src/less/*.less", "../avoindata-drupal-theme/less"],
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
