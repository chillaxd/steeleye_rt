#!/bin/sh
# $1 => python file name, without extension
# It will download required python packages inside the mentioned directory
# It will create a zip file from inside the target directory with only handler file and dependency
# It will remove the dependencies only from the directory

mkdir $1
pip install -r requirements.txt -t $1/ --no-cache-dir
cd $1
cp ../$1.py .
zip --exclude=*test* -r $1.zip *
mv $1.zip ../
cd ..
rm -rf $1