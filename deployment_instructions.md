# Deployment Instructions

Follow these steps to push your project to GitHub and prepare it for deployment on platforms like Render.

## 1. Prepare for GitHub

Since your project is already a Git repository, follow these commands in your terminal:

```bash
# Add all the mobile-compatibility changes I made
git add .

# Commit your changes with a descriptive message
git commit -m "Enhance mobile compatibility and add build script"

# Push the changes to your main branch on GitHub
git push origin main
```

## 2. Using the `build.sh` script

The `build.sh` file I created automates the following during deployment:
- **Dependency Installation**: `pip install -r requirements.txt`
- **Database Migrations**: `python manage.py migrate`
- **Static Assets**: `python manage.py collectstatic --no-input`

### Configuration for Render/Heroku:
- **Build Command**: `./build.sh` (You may need to run `chmod +x build.sh` first)
- **Start Command**: `gunicorn traffic_prediction.wsgi:application`

## 3. Recommended Production Checklist

1.  **Security**: Set `DEBUG = False` in `settings.py` for your production environment.
2.  **Environment Variables**: Ensure you define `TOMTOM_API_KEY` on your hosting platform's dashboard.
3.  **Static Files**: WhiteNoise is already set up to serve your CSS/JS files once `collectstatic` runs.

## 4. Mobile App (React Native)
If you are also deploying the mobile app:
- Ensure the `API_URL` in `src/config.js` matches your live Render link.
- Use `npm install` and `npx expo start` to test it locally.
