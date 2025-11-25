const express = require('express');
const jwt = require('jsonwebtoken');
const cookieParser = require('cookie-parser');

const app = express();
const port = process.env.PORT || 3000;

app.use(cookieParser());

function extractToken(req) {
    const authHeader = req.headers['authorization'];
    if (authHeader && typeof authHeader === 'string') {
        const parts = authHeader.split(' ');
        if (parts.length === 2 && /^bearer$/i.test(parts[0])) {
            return parts[1];
        }
    }
    return req.cookies ? req.cookies['auth-token'] : undefined;
}

app.get('/verify', (req, res) => {
    console.log('\n--- New verification request ---');
    console.log('Request Time:', new Date().toISOString());
    console.log('Request Headers Authorization:', req.headers['authorization'] || 'none');
    console.log('Request Cookies:', req.cookies || {});

    const token = extractToken(req);

    if (!token) {
        console.log('Result: Failure - No auth token found (cookie or header).');
        return res.status(401).send('Unauthorized: No token provided');
    }

    console.log('Auth token found. Proceeding to verification...');

    const jwtSecret = process.env.JWT_SECRET;
    if (!jwtSecret) {
        console.error('FATAL: JWT_SECRET is not defined in environment variables');
        return res.status(500).send('Internal Server Error: JWT secret not configured');
    }

    try {
        const payload = jwt.verify(token, jwtSecret, {
            issuer: 'xipilabs-auth',
            audience: 'xipilabs-products',
        });

        console.log('Result: Success - JWT verification successful.');
        console.log('Payload subject (user_id):', payload.sub);

        if (payload.sub) {
            res.setHeader('X-User-ID', payload.sub);
        }
        if (payload.email) {
            res.setHeader('X-User-Email', payload.email);
        }
        if (payload.phone) {
            res.setHeader('X-User-Phone', payload.phone);
        }

        res.status(200).send('OK');
    } catch (err) {
        console.log('Result: Failure - JWT verification failed.');
        console.error('JWT Error:', err.message);
        return res.status(401).send('Unauthorized: Invalid token');
    }
});

app.listen(port, () => {
    console.log(`Auth service listening on port ${port}`);
});
