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
var uglify = require("gulp-uglify");
var base64 = require("gulp-base64");
var pump = require("pump");

var paths = {
  src: {
    images: "src/images/**/*",
    ckan: "src/less/ckan",
    drupal: "../avoindata-drupal-theme/less/style.less",
    templates: "src/templates/**/*",
    static_pages: "src/static_pages",
    font: "src/font/**/*",
    fonts: "src/fonts/**/*",
    scripts: "src/scripts/**/*",
    bootstrap: "src/less/upstream_bootstrap",
    root: "src"
  },
  dist: "resources"
};

var timestamp = new Date().getTime();

gulp.task("clean", done => {
  del.sync([paths.dist]);
  done();
});

gulp.task("ckan", (done) => {
  pump([
    gulp.src(paths.src.ckan + "/*.less"),
    sourcemaps.init(),
    less({paths: [paths.src.ckan]}),
    prefixer({browsers: ['last 2 versions']}),
    template(),
    cleancss({ keepBreaks: false }),
    concat("ckan.css"),
    sourcemaps.write("./maps"),
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
    prefixer({browsers: ['last 2 versions']}),
    template({ timestamp: timestamp }),
    cleancss({ keepBreaks: false }),
    concat("style.css"),
    sourcemaps.write("./maps"),
    gulp.dest("../avoindata-drupal-theme/css"),
  ], done)
});

gulp.task("images", (done) => {
  pump([
    gulp.src(paths.src.images),
    imagemin([
      imagemin.gifsicle(),
      imagemin.jpegtran(),
      imagemin.optipng(),
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

gulp.task("static_css", (done) => {
  pump([
    gulp.src(paths.src.static_pages + "/css/main.css"),
    base64({ maxImageSize: 512 * 1024 }),
    concat("style.css"),
    gulp.dest(paths.src.static_pages + "/css")
  ], done)
});

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
    gulp.src(paths.src.scripts),
    gulp.dest(paths.dist + "/scripts")
  ], done)
});

gulp.task("bootstrap", (done) => {
  pump([
    gulp.src(paths.src.bootstrap + "/bootstrap.less"),
    less({paths: [paths.src.bootstrap]}),
    concat("bootstrap.css"),
    gulp.dest(paths.dist + "/vendor"),
    cleancss({ keepBreaks: false }),
    concat("bootstrap.min.css"),
    gulp.dest(paths.dist + "/vendor")
  ], done)
});

gulp.task("vendor", (done) => {
  pump([
    gulp.src(paths.src.root + "/vendor/**/*"),
    gulp.dest(paths.dist + "/vendor"),
  ], done)
});

gulp.task(
  "minify-vendor-javascript",
  gulp.series("vendor", (done) => {
    pump([
      gulp.src(paths.dist + "/vendor/**/*.js"),
      uglify(),
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
    gulp.parallel(
      "bootstrap",
      "minify-vendor-javascript",
      "templates",
      "static_pages",
      "images",
      "ckan",
      "drupal",
      "fonts",
      "font",
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
      "bootstrap",
      "vendor",
      "static_pages",
      "ckan",
      "drupal"
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
      "drupal"
    )
  );

  watcher.on("change", event => {
    console.log(
      "File " + event.path + " was " + event.type + ", running tasks..."
    );
  });
});
