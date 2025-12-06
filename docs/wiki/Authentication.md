# Authentication

User authentication system for ImageMagick WebGUI.

---

## Overview

The app supports:
- Email/password registration and login
- Google OAuth (optional)
- JWT token-based sessions
- Guest mode (limited features)

---

## Registration

### Standard Registration

1. Go to `/register`
2. Enter:
   - Email address
   - Password (min 8 characters)
   - Name (optional)
3. Click **Register**
4. Automatically logged in

### Requirements

| Field | Requirements |
|-------|--------------|
| Email | Valid email format, unique |
| Password | Min 8 characters |
| Name | Optional, max 100 chars |

---

## Login

### Email/Password Login

1. Go to `/login`
2. Enter email and password
3. Click **Login**
4. Redirected to dashboard

### Google OAuth

If configured:
1. Click **"Continue with Google"**
2. Select Google account
3. Authorize access
4. Redirected to dashboard

---

## JWT Tokens

### How It Works

```
1. User logs in
2. Server generates JWT token
3. Token stored in browser (httpOnly cookie)
4. Token sent with each request
5. Server validates token
6. Access granted or denied
```

### Token Details

| Property | Value |
|----------|-------|
| Algorithm | HS256 |
| Expiration | 60 minutes (configurable) |
| Storage | httpOnly cookie |
| Refresh | Automatic on activity |

### Token Expiration

```env
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

After expiration:
- User redirected to login
- All tokens invalidated

---

## Guest Mode

Without login, users can:
- ✅ Upload images
- ✅ Process images
- ✅ Download results
- ❌ Save to history
- ❌ Access settings
- ❌ Persistent storage

---

## API Authentication

### Obtaining Token

```http
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=yourpassword
```

Response:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

### Using Token

```http
GET /api/images
Authorization: Bearer eyJ...
```

### Token Validation

```http
GET /api/auth/me
Authorization: Bearer eyJ...
```

Response:
```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "John Doe",
  "created_at": "2024-12-05T10:00:00Z"
}
```

---

## Google OAuth Setup

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create new project
3. Enable **Google+ API**

### 2. Configure OAuth Consent

1. Go to **APIs & Services** → **OAuth consent screen**
2. Select **External**
3. Fill in app information
4. Add scopes: `email`, `profile`

### 3. Create Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. Select **Web application**
4. Add authorized redirect URIs:
   - `http://localhost:3000/api/auth/google/callback` (dev)
   - `https://yourdomain.com/api/auth/google/callback` (prod)

### 4. Configure Environment

```env
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
```

---

## Security Features

### Password Hashing

- Algorithm: bcrypt
- Salt rounds: 12
- Passwords never stored in plain text

### Rate Limiting

| Endpoint | Limit |
|----------|-------|
| Login | 5 attempts / minute |
| Register | 3 attempts / minute |
| API | 100 requests / minute |

### CORS

Configured for frontend origin only:
```python
allow_origins=["http://localhost:3000"]
```

### HTTPS

⚠️ **Production:** Always use HTTPS
- Encrypts tokens in transit
- Required for secure cookies
- Prevents MITM attacks

---

## Logout

### Web Interface

1. Click user menu (top right)
2. Select **Logout**
3. Token invalidated
4. Redirected to login

### API

```http
POST /api/auth/logout
Authorization: Bearer eyJ...
```

---

## Password Reset

Currently not implemented. Options:
1. Admin resets via database
2. Re-register with same email (if allowed)

Future: Email-based reset flow

---

## Session Management

### Active Sessions

Sessions are stateless (JWT):
- No server-side session storage
- Each token is self-contained
- Cannot list active sessions

### Force Logout All

Change `SECRET_KEY` in environment:
```env
SECRET_KEY=new-secret-key
```

All existing tokens become invalid.

---

## Troubleshooting

### Can't Login

1. Check email/password correct
2. Clear browser cookies
3. Check backend logs
4. Verify database connection

### Token Expired

- Re-login to get new token
- Increase `ACCESS_TOKEN_EXPIRE_MINUTES`

### Google OAuth Not Working

1. Check `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`
2. Verify redirect URI matches exactly
3. Check Google Cloud Console for errors
4. Ensure APIs enabled

### CORS Errors

1. Check frontend URL matches `allow_origins`
2. Verify no trailing slashes
3. Check protocol (http vs https)

---

## Best Practices

1. **Strong passwords** - Use password manager
2. **HTTPS in production** - Always encrypt traffic
3. **Short token expiry** - 30-60 minutes recommended
4. **Monitor logs** - Watch for failed login attempts
5. **Regular key rotation** - Change SECRET_KEY periodically

---

## Next Steps

- [[Configuration]] - Environment variables
- [[Security]] - Security best practices
- [[REST API]] - API documentation
