#!/bin/bash

## Copyright (C) 2021 Inryatt
## 
## This program is free software: you can redistribute it and/or modify it
## under the terms of the GNU General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
## 
## This program is distributed in the hope that it will be useful, but
## WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
## 
## You should have received a copy of the GNU General Public License
## along with this program.  If not, see
## <https://www.gnu.org/licenses/>.

## Author: Camila <inryatt@somewhere>
## Created: 2021-06-25

# dont break it

docker rm -f w1 2>/dev/null >/dev/null
docker rm -f w3 2>/dev/null >/dev/null
docker rm -f w2 2>/dev/null >/dev/null
docker build --tag proj . >/dev/null 
cd server
docker rm -f server 2>/dev/null >/dev/null
docker build --tag server . >/dev/null
cd ..
rm times.txt
rm tmp.txt
rm tmp2.txt 
touch times.txt 
touch tmp.txt
touch tmp2.txt 
for i in {1..50}
do
    echo next try
    cd server
    docker run -d  --name server  --rm server 2>/dev/null >/dev/null
    cd ..
    docker run -d  --name w3 --rm proj 2>/dev/null >/dev/null
    docker run -d   --name w2 --rm proj 2>/dev/null >/dev/null
    { time docker run --name w1  --rm proj >w1output.txt ;}  2> tmp.txt
    grep -v '^[[:blank:]]*$' tmp.txt > tmp2.txt
    head -1 tmp2.txt >> times.txt
    cd server
    docker rm -f server 2>/dev/null >/dev/null
    cd ..

    docker rm -f w1 2>/dev/null
    docker rm -f w3 2>/dev/null
    docker rm -f w2 2>/dev/null
done
