# MovieZone Ad Page Setup Instructions

## Overview
This ad page is designed to work seamlessly with your MovieZone Telegram bot. It implements a 15-second timer system where users watch ads before downloading movies.

## Files Structure
```
ad_page/
├── index.html      # Main HTML page
├── script.js       # JavaScript functionality
├── style.css       # Styling
└── README.md       # This file
```

## How It Works
1. User clicks download link in your Telegram channel
2. Bot shows "Watch Ad & Download" button 
3. Button redirects to: `https://your-ad-page.com/?token=SECURE_TOKEN&uid=USER_ID`
4. User sees 15-second timer and ad content
5. After timer, user clicks "Continue to Bot"
6. Redirects back to bot with secure token
7. Bot validates token and sends movie file

## Deployment Instructions

### Option 1: GitHub Pages (Free)
1. Create a new repository on GitHub
2. Upload these 3 files: `index.html`, `script.js`, `style.css`
3. Go to repository Settings → Pages
4. Select "Deploy from a branch" → "main" → "/ (root)"
5. Your page will be available at: `https://username.github.io/repository-name/`

### Option 2: Netlify (Free)
1. Go to [netlify.com](https://netlify.com)
2. Drag and drop the `ad_page` folder to deploy
3. Get your custom URL

### Option 3: Vercel (Free)
1. Go to [vercel.com](https://vercel.com)
2. Upload the folder or connect GitHub repository
3. Deploy and get your URL

## Configuration

### Update Bot Configuration
In your bot's `config.py`, update the AD_PAGE_URL:
```python
AD_PAGE_URL = "https://your-actual-domain.com"
```

### Update Ad Page Bot Username
In `script.js`, line 5:
```javascript
const BOT_USERNAME = "MoviezoneDownloadbot"; // Your actual bot username
```

## Adding Real Ads

Replace the placeholder comments in `index.html` with your actual ad code:

```html
<!-- [Place Banner Ad Here] -->
<!-- Replace with: <script>/* Your ad network code */</script> -->

<!-- [Place Social Bar Ad Here] -->
<!-- Replace with your social media ad code -->

<!-- [Place Native Banner Ad Here] -->
<!-- Replace with your native ad code -->
```

## Testing the Integration

1. Deploy the ad page to your hosting service
2. Update the `AD_PAGE_URL` in bot config
3. Restart the bot
4. Add a test movie with download links
5. Click the download link to test the full flow

## Security Features

- Secure token generation (32-character hash)
- Token expiry (24 hours)
- User ID validation
- One-time use tokens
- HTTPS redirect protection

## Mobile Responsive
The page is fully responsive and works perfectly on:
- Desktop browsers
- Mobile phones
- Tablets
- Telegram in-app browser

## Customization

### Change Timer Duration
In `script.js`, line 4:
```javascript
const COUNTDOWN_SECONDS = 15; // Change to your preferred duration
```

### Update Channel Link
In `index.html`, find the Telegram section and update:
```html
<a href="https://t.me/moviezone969" target="_blank" class="telegram-link">t.me/moviezone969</a>
```

### Modify Colors/Design
Edit the CSS variables in `style.css` to match your brand colors.

## Troubleshooting

### "Invalid or missing link parameters" Error
- Check that `AD_PAGE_URL` in config.py matches your deployed URL
- Ensure no trailing slash in the URL
- Verify bot is generating tokens correctly

### "Token not found" Error
- Check bot database permissions
- Verify token validation function is working
- Ensure tokens are being created before redirect

### Timer Not Working
- Check browser console for JavaScript errors
- Verify script.js is loading correctly
- Test in different browsers

## Support
If you need help with deployment or customization, refer to the bot documentation or check the console logs for error details.