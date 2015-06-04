var gulp = require('gulp'),
    runSequence = require('run-sequence'),
    watch = require('gulp-watch'),
    concat = require('gulp-concat'),
    imagemin = require('gulp-imagemin'),
    less = require('gulp-less'),
    sourcemaps = require('gulp-sourcemaps'),
    prefixer = require('gulp-autoprefixer'),
    del = require('del'),
    template = require('gulp-template'),
    inlineCss = require('gulp-inline-css'),
    MinCSS = require('gulp-minify-css'),
    base64 = require('gulp-base64');

var paths = {
  src: {
    images: 'src/images/**/*',
    less: 'src/less',
    templates: 'src/templates/**/*',
    static_pages: 'src/static_pages',
    fonts: 'src/fonts/**/*',
    scripts: 'src/scripts/**/*',
    bootstrap: 'src/less/upstream_bootstrap',
    root: 'src'
  },
  dist: 'resources'
};

var timestamp = new Date().getTime();

gulp.task('clean', function(cb) {
  del.sync([paths.dist]);
  cb();
});

gulp.task('less', function () {
  return gulp.src(paths.src.less+"/*.less")
    .pipe(sourcemaps.init())
    .pipe(less({
      paths: [ paths.src.less ]
    }))
    .pipe(prefixer('last 2 versions', 'ie 9'))
    .pipe(template({timestamp: timestamp}))
    .pipe(concat("main.css"))
    .pipe(sourcemaps.write('./maps'))
    .pipe(gulp.dest(paths.dist+'/styles'));
});

gulp.task('images', function() {
  return gulp.src(paths.src.images)
    .pipe(imagemin({optimizationLevel: 0}))
    .pipe(gulp.dest(paths.dist+'/images'));
});

gulp.task('templates', function() {
  return gulp.src(paths.src.templates)
    .pipe(template({timestamp: timestamp}))
    .pipe(gulp.dest(paths.dist+'/templates'));
});


gulp.task('static_css', function(){
  return gulp.src(paths.src.static_pages + "/css/main.css" )
    .pipe(base64({maxImageSize:512*1024}))
    .pipe(concat('style.css'))
    .pipe(gulp.dest(paths.src.static_pages + "/css"));
});

gulp.task('static_pages', ['static_css'], function() {
  return gulp.src(paths.src.static_pages + "/*.html")
    .pipe(inlineCss())
    .pipe(gulp.dest(paths.dist + '/static'));
});

gulp.task('fonts', function() {
  return gulp.src(paths.src.fonts)
    .pipe(gulp.dest(paths.dist+'/fonts'));
});

gulp.task('scripts', function() {
    return gulp.src(paths.src.scripts)
        .pipe(gulp.dest(paths.dist+'/scripts'));
});
asdfa = 2;

gulp.task('bootstrap', function(){
  return gulp.src(paths.src.bootstrap + '/bootstrap.less')
    .pipe(less({
      paths: [paths.src.bootstrap]
    }))
    .pipe(concat('bootstrap.css'))
    .pipe(gulp.dest(paths.dist + '/vendor'))
    .pipe(MinCSS({keepBreaks: false}))
    .pipe(concat('bootstrap.min.css'))
    .pipe(gulp.dest(paths.dist + '/vendor'));
});

gulp.task('vendor', function(){
  return gulp.src(paths.src.root + '/vendor/**/')
    .pipe(gulp.dest(paths.dist + '/vendor'));
});

gulp.task('config', function(){
  return gulp.src(paths.src.root + '/resource.config')
    .pipe(gulp.dest(paths.dist));
});

gulp.task('default', function(callback) {
  runSequence('clean',
              ['bootstrap', 'vendor', 'config', 'templates', 'static_pages', 'images', 'less', 'fonts', 'scripts'],
              callback);
});

gulp.task('watch', function () {
  gulp.watch([paths.src.less+'/**/*.less', paths.src.templates], ['default']);
});
