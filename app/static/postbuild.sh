#!/usr/bin bash

npx postcss ./dist/easy_read.css --use autoprefixer -d ./css
uglifycss ./dist/easy_read.css --output ./dist/easy_read.css
