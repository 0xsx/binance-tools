"use strict";

// Require build packages.
var
  autoprefixer = require("gulp-autoprefixer"),
  concat       = require("gulp-concat"),
  cssnano      = require("gulp-cssnano"),
  gulp         = require("gulp"),
  eslint       = require("gulp-eslint"),
  filter       = require("gulp-filter"),
  htmllint     = require("gulp-html-lint"),
  htmlmin      = require("gulp-htmlmin"),
  notify       = require("gulp-notify"),
  plumber      = require("gulp-plumber"),
  sass         = require("gulp-sass"),
  sasslint     = require("gulp-sass-lint"),
  webpack      = require("webpack-stream"),
  uglify       = require("gulp-uglify");


// Define a handler that prints errors encountered by gulp-plumber.
var plumberOptions = {
  errorHandler: function(err) {
    notify.onError({
      title:    "Error",
      message:  "<%= error %>",
    })(err);
    this.emit('end');
  }
};





// File listings. --------------------------------------------------------------

var htmlFiles = [
  "./src/html/index.html"
];


var jsFiles = [
  "./src/js/app.js",
  
];
var entryIndex = 0;


var cssFiles = [
  "./src/scss/main.scss"
];








// Linter tasks. ---------------------------------------------------------------

gulp.task("eslint", function() {
  return gulp.src(jsFiles)
    .pipe(filter(["**", "!src/vendor/**"]))
    .pipe(eslint())
    .pipe(eslint.format())
    .pipe(eslint.failOnError());
});

gulp.task("htmllint", function() {
  return gulp.src(htmlFiles)
    .pipe(filter(["**", "!src/vendor/**"]))
    .pipe(htmllint())
    .pipe(htmllint.format())
    .pipe(htmllint.failOnError());
});

gulp.task("sasslint", function() {
  return gulp.src(cssFiles)
    .pipe(filter(["**", "!src/vendor/**"]))
    .pipe(sasslint({
      configFile: ".sasslintrc"
    }))
    .pipe(sasslint.format())
    .pipe(sasslint.failOnError());
});




// Javascript build tasks. -----------------------------------------------------

gulp.task("js-development", ["eslint"], function() {
  return gulp.src(jsFiles)
    .pipe(plumber(plumberOptions))
    .pipe(webpack({
      entry: jsFiles[entryIndex],
      output: {
        filename: "app.js",
      },
      mode: "development",
      module: {
        rules: [
          {
            test: /\.jsx?$/,
            exclude: /node_modules/,
            use: {
              loader: "babel-loader",
              options: {
                presets: ["@babel/preset-env", "@babel/preset-react"],
                "plugins": [
                  ["@babel/plugin-proposal-decorators", { "legacy": true }],
                ]
              }
            }
          }
        ]
      }
    }))
    .pipe(gulp.dest("dist/development"))
    .pipe(notify({ message: "JS/JSX built for development" }));
});

gulp.task("js-production", ["eslint"], function() {
  return gulp.src(jsFiles)
    .pipe(plumber(plumberOptions))
    .pipe(webpack({
      entry: jsFiles[entryIndex],
      output: {
        filename: "app.js",
      },
      mode: "production",
      module: {
        rules: [
          {
            test: /\.jsx?$/,
            exclude: /node_modules/,
            use: {
              loader: "babel-loader",
              options: {
                presets: ["@babel/preset-env", "@babel/preset-react"],
                "plugins": [
                  ["@babel/plugin-proposal-decorators", { "legacy": true }],
                ]
              }
            }
          }
        ]
      }
    }))
    .pipe(uglify())
    .pipe(gulp.dest("dist/production"))
    .pipe(notify({ message: "JS/JSX built for production" }));
});






// CSS build tasks. ------------------------------------------------------------

gulp.task("css-development", ["sasslint"], function() {
  return gulp.src(cssFiles)
    .pipe(plumber(plumberOptions))
    .pipe(sass())
    .pipe(autoprefixer({
      browsers: ["last 2 versions"],
    }))
    .pipe(concat("style.css"))
    .pipe(gulp.dest("dist/development"))
    .pipe(notify({ message: "SASS/CSS built for development" }));
});

gulp.task("css-production", ["sasslint"], function() {
  return gulp.src(cssFiles)
    .pipe(plumber(plumberOptions))
    .pipe(sass())
    .pipe(autoprefixer({
      browsers: ["last 2 versions"],
    }))
    .pipe(concat("style.css"))
    .pipe(gulp.dest("dist/production"))
    .pipe(cssnano())
    .pipe(notify({ message: "SASS/CSS built for production" }));
});









// HTML build tasks. -----------------------------------------------------------

gulp.task("html-development", ["htmllint"], function() {
  return gulp.src(htmlFiles)
    .pipe(plumber(plumberOptions))
    .pipe(gulp.dest("dist/development"))
    .pipe(notify({ message: "HTML built for development" }));
});

gulp.task("html-production", ["htmllint"], function() {
  return gulp.src(htmlFiles)
    .pipe(plumber(plumberOptions))
    .pipe(htmlmin({ collapseWhitespace: true }))
    .pipe(gulp.dest("dist/production"))
    .pipe(notify({ message: "HTML built for production" }));
});



// Image build tasks. ----------------------------------------------------------

gulp.task("img-development", function() {
  return gulp.src("src/img/**")
    .pipe(plumber(plumberOptions))
    .pipe(gulp.dest("dist/development/img"))
    .pipe(notify({ message: "Images built for development" }));
});

gulp.task("img-production", function() {
  return gulp.src("src/img/**")
    .pipe(plumber(plumberOptions))
    .pipe(gulp.dest("dist/production/img"))
    .pipe(notify({ message: "Images built for production" }));
});






// Build interface tasks. ------------------------------------------------------

gulp.task("dev", ["js-development", "html-development", "css-development", "img-development"]);
gulp.task("build", ["js-production", "html-production", "css-production", "img-production"]);
gulp.task("default", ["build"]);




// Watcher task. ---------------------------------------------------------------

gulp.task("watch", function() {

  gulp.watch("src/**/*.css",  ["css-development"]);
  gulp.watch("src/**/*.scss", ["css-development"]);
  gulp.watch("src/**/*.js*",   ["js-development"]);
  gulp.watch("src/**/*.html", ["html-development"]);
  gulp.watch("src/img/**", ["img-development"]);
  
});






