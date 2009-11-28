#!/bin/bash
#
# Source this script to build the SharedPaint-vX.X.agpkg3 file.
# Author: William A. Romero R. (wil-rome@uniandes.edu.co)
# -----------------------------------------------------------

project_name="SharedPaint"
project_version="3.0"
type="agpkg3"

in="./src"
out="../dist"

cd $in
zip "$project_name""-v$project_version"".$type" *.*
mv *."$type" $out 
