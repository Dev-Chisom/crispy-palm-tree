# Railway Base URL Guide

## How to Get Your Railway Service URL

### Step 1: Generate Domain

1. Go to Railway Dashboard
2. Click on your **crispy-palm-tree** service
3. Go to **Settings** tab
4. Scroll to **Networking** section → **Public Networking**
5. In "Enter the port your app is listening on":
   - Railway shows default `8080`
   - **Leave it as 8080** (Railway will route correctly)
   - OR check your deployment logs to see what port Railway assigned
   - Our app uses `$PORT` which Railway sets automatically
6. Click **"Generate Domain"** button

### Step 2: Railway Will Provide

Railway will generate a URL in this format:
```
https://[service-name]-[environment].up.railway.app
```

**Example:**
```
https://crispy-palm-tree-production.up.railway.app
```

### Step 3: Update CORS Settings

After getting your URL, update the `CORS_ORIGINS` variable:

1. Go to **crispy-palm-tree** → **Variables**
2. Find or add `CORS_ORIGINS`
3. Set value to:
   ```
   https://your-frontend-domain.com,https://crispy-palm-tree-production.up.railway.app
   ```

## API Endpoints

Once deployed, your API will be available at:

- **Base URL**: `https://crispy-palm-tree-production.up.railway.app`
- **Health Check**: `https://crispy-palm-tree-production.up.railway.app/health`
- **API Docs**: `https://crispy-palm-tree-production.up.railway.app/docs`
- **ReDoc**: `https://crispy-palm-tree-production.up.railway.app/redoc`
- **API v1**: `https://crispy-palm-tree-production.up.railway.app/api/v1`

## Frontend Integration

Update your frontend API configuration:

```javascript
// Example: Update your frontend API base URL
const API_BASE_URL = 'https://crispy-palm-tree-production.up.railway.app/api/v1';
```

## Custom Domain (Optional)

Railway also supports custom domains:

1. Go to **Settings** → **Networking**
2. Click **"Custom Domain"**
3. Add your domain (e.g., `api.yourdomain.com`)
4. Follow DNS configuration instructions

## Testing Your Deployment

After deployment, test these endpoints:

```bash
# Health check
curl https://crispy-palm-tree-production.up.railway.app/health

# API root
curl https://crispy-palm-tree-production.up.railway.app/

# List stocks
curl https://crispy-palm-tree-production.up.railway.app/api/v1/stocks
```

## Important Notes

- **HTTPS**: Railway provides HTTPS automatically
- **No Port**: Railway handles ports automatically (use default HTTPS port 443)
- **Environment Variables**: URL is available as `RAILWAY_PUBLIC_DOMAIN` if needed
- **Service Status**: URL only works when service is "Online"

## Troubleshooting

**Can't find Generate Domain?**
- Make sure service is deployed successfully
- Check that service status is "Online"
- Try refreshing the page

**URL not working?**
- Check service is running (not "Deploying" or "Failed")
- Verify health check endpoint works
- Check service logs for errors
