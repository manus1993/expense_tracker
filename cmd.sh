#!/bin/bash


if [ $1 == "format" ]
then
    python3 -m isort --multi-line 3 --trailing-comma --line-length 79 app
    python3 -m flake8 --max-line-length=79 app
    python3 -m black --line-length=79 app
elif [ $1 == "start" ]
then
    source .env.sh
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
elif [ $1 == "test" ]
then
    source .env.sh
    coverage run --source ./app -m pytest --disable-warnings
elif [ $1 == "tag-deploy" ]
then
    if [ $# -ne 2 ]
    then
        echo "No tag supplied, expected format: `./cmd.sh tag-deploy v1.0.0`"
    fi

    echo $2 > ./app/version.txt
    git add ./app/version.txt
    git commit -m "$2"
    git push

    git tag $2
    git push origin $2
else
   echo "unknown command $1"
fi
