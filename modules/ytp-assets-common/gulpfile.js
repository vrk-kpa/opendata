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

gulp.task("ckan", () => {
  return gulp
    .src(paths.src.ckan + "/*.less")
    .pipe(sourcemaps.init())
    .pipe(
      less({
        paths: [paths.src.ckan]
      })
    )
    .pipe(prefixer({
			browsers: ['last 2 versions']
		}))
    .pipe(template({ timestamp: timestamp }))
    .pipe(cleancss({ keepBreaks: false }))
    .pipe(concat("ckan.css"))
    .pipe(sourcemaps.write("./maps"))
    .pipe(gulp.dest(paths.dist + "/styles"));
});

// // Compiles Less files in Drupal theme directory
// // Output destination is also in Drupal theme directory
gulp.task("drupal", () => {
  return gulp
    .src(paths.src.drupal)
    .pipe(sourcemaps.init())
    .pipe(
      less({
        paths: [paths.src.drupal]
      })
    )
    .pipe(prefixer({
			browsers: ['last 2 versions']
		}))
    .pipe(template({ timestamp: timestamp }))
    .pipe(cleancss({ keepBreaks: false }))
    .pipe(concat("style.css"))
    .pipe(sourcemaps.write("./maps"))
    .pipe(gulp.dest("../avoindata-drupal-theme/css"));
});

gulp.task("images", () => {
  return gulp
    .src(paths.src.images)
    .pipe(imagemin({ optimizationLevel: 0 }))
    .pipe(gulp.dest(paths.dist + "/images"));
});

gulp.task("templates", () => {
  return gulp
    .src(paths.src.templates)
    .pipe(template({ timestamp: timestamp }))
    .pipe(gulp.dest(paths.dist + "/templates"));
});

gulp.task("static_css", () => {
  return gulp
    .src(paths.src.static_pages + "/css/main.css")
    .pipe(base64({ maxImageSize: 512 * 1024 }))
    .pipe(concat("style.css"))
    .pipe(gulp.dest(paths.src.static_pages + "/css"));
});

gulp.task(
  "static_pages",
  gulp.series("static_css", () => {
    return gulp
      .src(paths.src.static_pages + "/*.html")
      .pipe(inlineCss())
      .pipe(gulp.dest(paths.dist + "/static"));
  })
);

gulp.task("fonts", () => {
  return gulp.src(paths.src.fonts).pipe(gulp.dest(paths.dist + "/fonts"));
});

gulp.task("font", () => {
  return gulp.src(paths.src.font).pipe(gulp.dest(paths.dist + "/font"));
});

gulp.task("scripts", () => {
  return gulp.src(paths.src.scripts).pipe(gulp.dest(paths.dist + "/scripts"));
});

gulp.task("bootstrap", () => {
  return gulp
    .src(paths.src.bootstrap + "/bootstrap.less")
    .pipe(
      less({
        paths: [paths.src.bootstrap]
      })
    )
    .pipe(concat("bootstrap.css"))
    .pipe(gulp.dest(paths.dist + "/vendor"))
    .pipe(cleancss({ keepBreaks: false }))
    .pipe(concat("bootstrap.min.css"))
    .pipe(gulp.dest(paths.dist + "/vendor"));
});

gulp.task("vendor", done => {
  return gulp
    .src(paths.src.root + "/vendor/**/")
    .pipe(gulp.dest(paths.dist + "/vendor"));
  done();
});

gulp.task(
  "minify-vendor-javascript",
  gulp.series("vendor", () => {
    return gulp
      .src(paths.dist + "/vendor/**/*.js")
      .pipe(uglify())
      .pipe(gulp.dest(paths.dist + "/vendor"));
  })
);

gulp.task("config", () => {
  return gulp
    .src(paths.src.root + "/resource.config")
    .pipe(gulp.dest(paths.dist));
});

gulp.task(
  "default",
  gulp.series(
    "clean",
    gulp.parallel(
      "bootstrap",
      "vendor",
      "minify-vendor-javascript",
      "config",
      "templates",
      "static_pages",
      "images",
      "ckan",
      "drupal",
      "fonts",
      "font",
      "scripts"
    )
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
