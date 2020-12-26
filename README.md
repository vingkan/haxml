# HaxML

On-demand machine learning predictions for HaxClass data.

## Project Structure

- `server` contains the Flask app for serving predictions on-demand.

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
