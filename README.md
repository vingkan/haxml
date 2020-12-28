# HaxML

On-demand machine learning predictions for HaxClass data.

## Goal

Create and deploy machine learning models to predict “expected goals” (XG) in the online game [HaxBall](https://www.haxball.com/). XG is the probability of a given kick resulting in a goal and can be used to create higher-order metrics, for both offense and defense.

## Project Structure

This repository contains all the tools we need to build machine learning models for HaxBall:

- **Analysis:** Exploring data to find insights, creating offline reports.
- **Modeling:** Engineering features, training and evaluating classifiers.
- **Serving:** Deploying models to make predictions and explanations on-demand.

```
haxml
├── data/               Data for analysis and modeling (not committed).
├── haxml/              Python modules for analysis, modeling, and serving.
|   ├── prediction.py
|   ├── utils.py
|   └── viz.py
├── models/             Saved classifiers for use in modeling and serving.
├── notebooks/          Jupyter notebooks for analysis and modeling.
├── scripts/            Scripts to download and prepare data.
└── server/             Flask app for serving predictions on-demand.
```

## Data

Data is collected through a scraper built with the HaxBall headless API, from a hosted HaxBall room and stored in a Firebase real-time database. Data is stored in a "packed" format and can be "inflated" using the `haxml.utils.inflate_match(packed)` method.

Refer to the [HaxClass repository](https://github.com/vingkan/haxclass) for the schema of the inflated match data.

Players' gameplay data and usernames are collected, but not their chat messages. HaxML strips user names from the data when downloading from the database, but on-demand predictions retain the user names.

Visit the [HaxClass Hub](https://vingkan.github.io/haxclass/hub) to browse data from recent HaxBall matches in our hosted room and view XG time plots from the current production model.

## Helpful Commands

### First Time

Set up virtual environment to use local dependencies instead of global dependencies.

```bash
virtualenv venv
```

### Start Each Session

Activate your virtual environment.

```bash
source venv/bin/activate
```

### During Each Session

Start a local Jupyter notebook server.

```bash
jupyter notebook
```

Run the prediction server.

```bash
python server/__init__.py
```

Install the latest dependencies, if requirements.txt changed since your last session.

```bash
pip install -r requirements.txt
```

Update dependencies if you added a new dependency that others should have.

```bash
pip freeze > requirements.txt
```

### End Each Session

```bash
deactivate
```

### Getting Data Access

To download data from our database, you will need our read-only Firebase credentials. Ask Vinesh for the credentials and then add them to your `.env` file. This file is excluded in `.gitignore` to avoid accidentally committing them.

To create an `.env` file, run:

```bash
touch .env
```

And then edit it, to add the credentials:

```
PORT=5000
firebase_apiKey=YOUR_SECRET
firebase_authDomain=YOUR_SECRET
firebase_databaseURL=YOUR_SECRET
firebase_projectId=YOUR_SECRET
firebase_storageBucket=YOUR_SECRET
firebase_messagingSenderId=YOUR_SECRET
firebase_appId=YOUR_SECRET
```

### Getting Data

`Makefile` defines how the data files in this project are created. To create the data yourself, run:

```bash
make
```

This will trigger all the necessary commands and show you progress. Once data files are made, running `make` will not overwrite them. To build the data from scratch, run:

```bash
make clean
make
```

### Deploying

The HaxML Flask app is currently hosted on Heroku, on the free tier. You can wake it up by going to:

```
https://haxml.herokuapp.com/hello
```

Heroku is set to automatically build and deploy when we commit to the `main` branch of this repository. We will work in our own branches, submit pull requests, and then merge into `main` to deploy.

`Procfile` defines how the Flask app will start with the `web` command. If you have Heroku installed locally, you can test it by running:

```bash
heroku local web
```

If you have access to the `haxml` project on Heroku, you can check the Flask app logs with this command:

```bash
heroku logs --tail -a=haxml
```

And you can check usage of dyno hours on the free tier with this command:

```bash
heroku ps -a=haxml
```

We also have a Digital Ocean Droplet where we can run the HaxClass data collection system and deploy the HaxML Flask app, albeit without an SSL-secured domain.
